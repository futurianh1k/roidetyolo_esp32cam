# ESP-IDF v5.5.1 컴포넌트 수정 가이드

**작성일:** 2025-12-10

---

## 문제

ESP-IDF v5.5.1에서 `esp_camera` 컴포넌트를 찾을 수 없음:

```
Failed to resolve component 'esp_camera' required by component 'main':
unknown name.
```

---

## 해결 방법

### 1. idf_component.yml에 esp32-camera 추가

ESP-IDF v5.x에서는 `esp_camera`가 기본 포함되어 있지 않고, IDF Component Manager를 통해 설치해야 합니다.

`firmware_idf/main/idf_component.yml`:

```yaml
dependencies:
  # ESP32 Camera driver (required for ESP-IDF v5.x)
  espressif/esp32-camera: ^2.0.0
```

### 2. CMakeLists.txt에서 컴포넌트 이름 확인

`esp32-camera` 컴포넌트를 설치하면 `esp_camera` 또는 `esp32-camera`로 사용할 수 있습니다.

`firmware_idf/main/CMakeLists.txt`:

```cmake
REQUIRES
    ...
    esp32-camera  # 또는 esp_camera (컴포넌트에 따라 다름)
    ...
```

### 3. 컴포넌트 이름 확인 방법

빌드 시 오류 메시지를 확인하여 정확한 컴포넌트 이름을 확인하세요.

또는 다음 명령으로 확인:

```powershell
cd firmware_idf
idf.py show_efuse_table
```

---

## 컴포넌트 설치

컴포넌트는 빌드 시 자동으로 다운로드됩니다:

```powershell
cd firmware_idf
.\build.ps1
```

또는 수동으로:

```powershell
idf.py reconfigure
```

---

## 참고

- **ESP-IDF v5.x 변경사항**: 많은 컴포넌트가 IDF Component Manager로 이동
- **esp32-camera**: https://components.espressif.com/components/espressif/esp32-camera
- **컴포넌트 검색**: https://components.espressif.com/

---

**작성자:** AI Assistant  
**마지막 업데이트:** 2025-12-10
