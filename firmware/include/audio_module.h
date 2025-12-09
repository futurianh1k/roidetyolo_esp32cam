/**
 * 오디오 모듈 헤더
 */

#ifndef AUDIO_MODULE_H
#define AUDIO_MODULE_H

#include <Arduino.h>

// 오디오 초기화
bool audioInit();

// 마이크 제어
bool audioStartMicrophone();
void audioPauseMicrophone();
void audioStopMicrophone();

// ASR (음성인식) 모드
bool audioStartASRMode();
void audioStopASRMode();
bool audioIsASRMode();

// 스피커 제어
bool audioPlayURL(const char *url);
void audioStopSpeaker();
void audioSetVolume(uint8_t volume);

// 오디오 루프
void audioLoop();

#endif // AUDIO_MODULE_H
