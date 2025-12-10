/**
 * 카메라 모듈 헤더
 */

#ifndef CAMERA_MODULE_H
#define CAMERA_MODULE_H

#include <Arduino.h>

// 카메라 초기화
bool cameraInit();

// 카메라 제어
bool cameraStart();
void cameraPause();
void cameraStop();
void cameraLoop();

// 카메라 상태
bool isCameraActive();

// 영상 sink 설정
void cameraSetSink(const char *sinkUrl, const char *streamMode,
                   int frameInterval);
void cameraClearSink();
bool isCameraSinkActive();

#endif // CAMERA_MODULE_H
