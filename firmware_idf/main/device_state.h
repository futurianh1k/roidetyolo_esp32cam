#ifndef DEVICE_STATE_H
#define DEVICE_STATE_H

/**
 * Device State Definitions
 * 
 * 상태 머신에서 사용하는 디바이스 상태 정의
 */

enum DeviceState {
    kDeviceStateUnknown = 0,
    kDeviceStateStarting,      // 초기화 중
    kDeviceStateIdle,          // 대기 상태
    kDeviceStateConnecting,    // 네트워크 연결 중
    kDeviceStateConnected,     // 네트워크 연결됨
    kDeviceStateListening,     // 음성 인식 대기 중
    kDeviceStateProcessing,    // 음성 처리 중
    kDeviceStateSpeaking,       // 음성 출력 중
    kDeviceStateCameraActive,   // 카메라 활성
    kDeviceStateError,          // 오류 상태
};

#endif // DEVICE_STATE_H

