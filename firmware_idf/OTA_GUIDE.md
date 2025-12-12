# OTA (Over-The-Air) 업데이트 가이드

## M5Stack CoreS3 OTA 설정

### 파티션 레이아웃 (16MB Flash)

| Partition | Type        | Offset   | Size    | 설명                   |
| --------- | ----------- | -------- | ------- | ---------------------- |
| nvs       | data/nvs    | 0x9000   | 16KB    | Non-Volatile Storage   |
| otadata   | data/ota    | 0xD000   | 8KB     | OTA 상태 정보          |
| phy_init  | data/phy    | 0xF000   | 4KB     | WiFi PHY 초기화        |
| **ota_0** | app/ota_0   | 0x10000  | **4MB** | 앱 파티션 0 (현재)     |
| **ota_1** | app/ota_1   | 0x410000 | **4MB** | 앱 파티션 1 (업데이트) |
| spiffs    | data/spiffs | 0x810000 | ~8MB    | 파일 시스템            |

### OTA 특징

- ✅ **Rollback 지원**: 새 펌웨어가 부팅 실패 시 자동으로 이전 버전으로 복귀
- ✅ **듀얼 파티션**: 안전한 업데이트 (한 파티션에서 실행, 다른 파티션에 업데이트)
- ✅ **충분한 공간**: 각 4MB (현재 펌웨어 ~1.1MB, 향후 확장 가능)

## OTA 업데이트 방법

### 1. HTTPS OTA 서버 방식

```cpp
#include "esp_https_ota.h"
#include "esp_ota_ops.h"

void perform_ota_update(const char* firmware_url) {
    esp_http_client_config_t config = {
        .url = firmware_url,
        .cert_pem = (char *)server_cert_pem_start,
    };

    esp_https_ota_config_t ota_config = {
        .http_config = &config,
    };

    esp_err_t ret = esp_https_ota(&ota_config);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "OTA Succeed, Rebooting...");
        esp_restart();
    } else {
        ESP_LOGE(TAG, "OTA Failed");
    }
}
```

**서버 설정 예시:**

```bash
# 펌웨어를 HTTPS 서버에 업로드
https://your-server.com/firmware/cores3-management-v1.0.1.bin
```

### 2. MQTT OTA 방식 (추천)

현재 MQTT 인프라를 활용하여 OTA 명령 전송:

```json
// MQTT Topic: devices/{device_id}/command
{
  "type": "ota_update",
  "firmware_url": "https://your-server.com/firmware/latest.bin",
  "version": "1.0.1",
  "checksum": "sha256:abcdef..."
}
```

**구현 예시:**

```cpp
void handle_ota_command(const std::string& payload) {
    cJSON* json = cJSON_Parse(payload.c_str());
    const char* firmware_url = cJSON_GetObjectItem(json, "firmware_url")->valuestring;
    const char* version = cJSON_GetObjectItem(json, "version")->valuestring;

    ESP_LOGI(TAG, "Starting OTA update to version %s", version);
    perform_ota_update(firmware_url);

    cJSON_Delete(json);
}
```

### 3. HTTP 파일 업로드 방식

웹 인터페이스를 통한 로컬 업데이트:

```cpp
#include "esp_http_server.h"

esp_err_t ota_upload_handler(httpd_req_t *req) {
    esp_ota_handle_t ota_handle;
    const esp_partition_t *update_partition = esp_ota_get_next_update_partition(NULL);

    esp_ota_begin(update_partition, OTA_SIZE_UNKNOWN, &ota_handle);

    char buf[1024];
    int received;
    while ((received = httpd_req_recv(req, buf, sizeof(buf))) > 0) {
        esp_ota_write(ota_handle, buf, received);
    }

    esp_ota_end(ota_handle);
    esp_ota_set_boot_partition(update_partition);

    httpd_resp_send(req, "OTA Update Success", HTTPD_RESP_USE_STRLEN);
    esp_restart();

    return ESP_OK;
}
```

### 4. 로컬 파일 시스템 방식

SPIFFS/SD 카드에서 펌웨어 로드:

```cpp
void ota_from_file(const char* file_path) {
    FILE* file = fopen(file_path, "rb");
    if (!file) return;

    esp_ota_handle_t ota_handle;
    const esp_partition_t *update_partition = esp_ota_get_next_update_partition(NULL);
    esp_ota_begin(update_partition, OTA_SIZE_UNKNOWN, &ota_handle);

    char buf[1024];
    size_t read_len;
    while ((read_len = fread(buf, 1, sizeof(buf), file)) > 0) {
        esp_ota_write(ota_handle, buf, read_len);
    }

    fclose(file);
    esp_ota_end(ota_handle);
    esp_ota_set_boot_partition(update_partition);
    esp_restart();
}
```

## OTA 안전성 확인

### 1. 부트 파티션 확인

```cpp
const esp_partition_t *running = esp_ota_get_running_partition();
ESP_LOGI(TAG, "Running partition: %s at offset 0x%x",
         running->label, running->address);
```

### 2. OTA 상태 확인

```cpp
esp_ota_img_states_t ota_state;
if (esp_ota_get_state_partition(running, &ota_state) == ESP_OK) {
    if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
        ESP_LOGI(TAG, "New firmware, marking as valid");
        esp_ota_mark_app_valid_cancel_rollback();
    }
}
```

### 3. Rollback 기능

```cpp
// 펌웨어가 정상 작동하지 않으면 자동 rollback
// 또는 수동 rollback:
const esp_partition_t *last_invalid = esp_ota_get_last_invalid_partition();
esp_ota_set_boot_partition(last_invalid);
esp_restart();
```

## 빌드 및 배포

### 1. 펌웨어 빌드

```powershell
cd d:\cursorworks\roidetyolo_esp32cam\firmware_idf
.\build.ps1
```

생성된 파일: `build/cores3-management.bin`

### 2. 버전 관리

펌웨어에 버전 정보 포함:

```cpp
// version.h
#define FIRMWARE_VERSION "1.0.1"
#define BUILD_DATE __DATE__
#define BUILD_TIME __TIME__
```

### 3. 배포 체크리스트

- [ ] 버전 번호 업데이트
- [ ] 변경 로그 작성
- [ ] 테스트 기기에서 검증
- [ ] SHA256 체크섬 생성
- [ ] 서버에 업로드
- [ ] MQTT 명령 전송

## 모니터링

### OTA 진행 상황 로그

```
I (12345) OTA: Starting OTA update...
I (12456) OTA: Writing to partition 'ota_1' at offset 0x410000
I (23456) OTA: Downloaded 524288 / 1048576 bytes (50%)
I (34567) OTA: Downloaded 1048576 / 1048576 bytes (100%)
I (34678) OTA: OTA Update Complete
I (34789) OTA: Setting boot partition to 'ota_1'
I (34890) OTA: Rebooting in 5 seconds...
```

### MQTT 상태 보고

```json
{
  "type": "ota_progress",
  "progress": 50,
  "status": "downloading",
  "bytes_downloaded": 524288,
  "total_bytes": 1048576
}
```

## 참고 자료

- [ESP-IDF OTA 공식 문서](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/system/ota.html)
- [M5Stack CoreS3 OTA 예제](https://github.com/m5stack/M5CoreS3/tree/main/examples/OTA)
- 프로젝트 OTA 구현: `firmware_idf/main/network/ota_service.cc` (예정)

## 문제 해결

### OTA 실패 시

1. 파티션 테이블 확인: `idf.py partition-table`
2. 펌웨어 크기 확인: 4MB 이하인지 체크
3. HTTPS 인증서 확인
4. 네트워크 연결 확인
5. 로그 확인: `idf.py monitor`

### Rollback 강제 실행

```bash
# esptool로 이전 파티션 지정
esptool.py --chip esp32s3 --port COM3 write_flash 0xd000 otadata_previous.bin
```
