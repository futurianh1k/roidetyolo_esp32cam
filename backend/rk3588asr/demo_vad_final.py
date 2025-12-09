# -*- coding: utf-8 -*-
"""
Sherpa-ONNX Sense-Voice RKNN Speech Recognition Web UI for RK3588
Offline Recognizer + 청크 기반 스트리밍 처리 (v4 - CSV 리포트 기능 추가)

🔧 v4 개선 사항:
1. 마이크 실시간 음성인식 세션 결과 누적 기능
2. 마이크 세션용 CSV 리포트 자동 생성
3. 배치 테스트용 CSV 리포트 자동 생성
4. UI에 CSV 다운로드 버튼 추가
5. 세션별 결과 관리 및 초기화 기능
"""

import os
import warnings
import gradio as gr
import numpy as np
from datetime import datetime
import soundfile as sf
import wave
import queue
import threading
import time
from collections import deque

# 자체 서명 인증서 사용 시 Gradio 내부 API 호출 SSL 검증 비활성화
os.environ['GRADIO_SSL_VERIFY'] = 'false'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['PYTHONHTTPSVERIFY'] = '0'
# httpx SSL 검증 비활성화 (자체 서명 인증서 사용 시)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# httpx 클라이언트의 SSL 검증 비활성화를 위한 패치
try:
    import httpx
    # httpx의 기본 SSL 검증 비활성화
    original_init = httpx.Client.__init__
    def patched_init(self, *args, verify=False, **kwargs):
        return original_init(self, *args, verify=False, **kwargs)
    httpx.Client.__init__ = patched_init
    
    original_async_init = httpx.AsyncClient.__init__
    def patched_async_init(self, *args, verify=False, **kwargs):
        return original_async_init(self, *args, verify=False, **kwargs)
    httpx.AsyncClient.__init__ = patched_async_init
except ImportError:
    pass

from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Optional
import re
import json
import logging
import csv
import uuid
import requests

# jiwer는 선택적 의존성으로 처리
try:
    from jiwer import compute_measures
    JIWER_AVAILABLE = True
except ImportError:
    compute_measures = None
    JIWER_AVAILABLE = False
    print("[WARN] jiwer 라이브러리를 찾을 수 없습니다. `pip install jiwer` 로 설치하세요.")


warnings.filterwarnings("ignore")

# ====================
# 로깅 설정
# ====================
logging.basicConfig(
    level=logging.INFO,  # DEBUG 레벨로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# sherpa-onnx import
try:
    import sherpa_onnx
except ImportError:
    raise ImportError(
        "sherpa-onnx를 찾을 수 없습니다.\n"
        "다음 명령어로 설치해주세요:\n"
        "pip install sherpa-onnx -f https://k2-fsa.github.io/sherpa/onnx/rk-npu.html"
    )

# ====================
# 전역 설정
# ====================
MODEL_DIR = os.path.join(
    os.getcwd(),
    "models",
    "sherpa-onnx-rk3588-30-seconds-sense-voice-zh-en-ja-ko-yue-2024-07-17",
)

MODEL_PATH = os.path.join(MODEL_DIR, "model.rknn")
TOKENS_PATH = os.path.join(MODEL_DIR, "tokens.txt")

# 전역 recognizer 변수
recognizer = None

# ====================
# 🔹 응급 상황 API 설정
# ====================
EMERGENCY_API_CONFIG = {
    "enabled": True,  # API 호출 활성화 여부
    "api_endpoints": [
        {
            "name": "Emergency Alert API (JSON)",
            "url": "http://10.10.11.23:10008/api/emergency/quick",
            "enabled": True,
            "method": "POST",
            "type": "json"
        },
        {
            "name": "Emergency Alert API (Multipart)",
            "url": "http://10.10.11.23:10008/api/emergency/quick/{watchId}",
            "enabled": True,
            "method": "POST",
            "type": "multipart"
        }
    ],
    "watch_id": "watch_1764653561585_7956",
    "sender_id": "voice_asr_system",
    "include_image_url": True,
    "image_base_url": "http://10.10.11.79:8080/api/images",
    "fcm_project_id": "emergency-alert-system-f27e6",
}


def send_emergency_alert(recognized_text: str, emergency_keywords: List[str]):
    """
    응급 상황 감지 시 API로 이벤트 전송
    
    Args:
        recognized_text: 음성 인식 결과 텍스트
        emergency_keywords: 감지된 응급 키워드 리스트
    """
    if not EMERGENCY_API_CONFIG.get("enabled", False):
        logger.info("⚠️ 응급 API 호출이 비활성화되어 있습니다.")
        return
    
    config = EMERGENCY_API_CONFIG
    enabled_endpoints = [ep for ep in config.get("api_endpoints", []) if ep.get("enabled", False)]
    
    if not enabled_endpoints:
        logger.warning("⚠️ 활성화된 API 엔드포인트가 없습니다.")
        return
    
    # JSON 타입 API 우선 선택
    selected_api = None
    for ep in enabled_endpoints:
        if ep.get("type") == "json":
            selected_api = ep
            break
    
    if not selected_api and enabled_endpoints:
        selected_api = enabled_endpoints[0]
    
    if not selected_api:
        logger.warning("⚠️ 사용 가능한 API 엔드포인트가 없습니다.")
        return
    
    try:
        logger.info(f"🚨 응급 상황 감지! API 호출 시작: {selected_api['name']}")
        logger.info(f"   - 인식 텍스트: {recognized_text}")
        logger.info(f"   - 감지 키워드: {', '.join(emergency_keywords)}")
        
        # 이벤트 데이터 생성
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        watch_id = config.get("watch_id", "watch_default")
        sender_id = config.get("sender_id", "voice_asr_system")
        
        if selected_api.get("type") == "json":
            # JSON 방식
            api_url = selected_api['url']
            if '{watchId}' in api_url:
                api_url = api_url.replace('{watchId}', watch_id)
            elif watch_id not in api_url:
                if not api_url.endswith('/'):
                    api_url += '/'
                api_url += watch_id
            
            # 이미지 URL 생성 (선택적)
            image_url = None
            if config.get("include_image_url", False):
                image_base = config.get("image_base_url", "http://10.10.11.79:8080/api/images")
                image_filename = f"emergency_{event_id.split('-')[0]}.jpeg"
                image_url = f"{image_base}/{image_filename}"
            
            # 서버가 기대하는 형식으로만 데이터 구성
            request_data = {
                "senderId": sender_id,
                "note": f"응급 상황 감지: {recognized_text} (키워드: {', '.join(emergency_keywords)})",
                "imageUrl": image_url  # null 가능
            }
            
            logger.info(f"📤 API 요청 URL: {api_url}")
            logger.info(f"📤 요청 데이터: {request_data}")

            # ✅ 수정: api_url 사용 및 requests.post() 사용
            response = requests.post(
                url=api_url,  # ✅ 수정: api_url 사용
                json=request_data,  # ✅ 수정: 서버가 기대하는 필드만
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            logger.info(f"✅ API 호출 성공 (Status: {response.status_code})")
            logger.info(f"   - Event ID: {event_id}")
            logger.info(f"   - Response: {response.text[:200]}")
        
        else:
            # Multipart 방식
            api_url = selected_api['url']
            if '{watchId}' in api_url:
                api_url = api_url.replace('{watchId}', watch_id)
            elif watch_id not in api_url:
                if not api_url.endswith('/'):
                    api_url += '/'
                api_url += watch_id
            
            # 쿼리 파라미터로 senderId와 note 추가
            import urllib.parse
            note_text = f"응급 상황 감지: {recognized_text} (키워드: {', '.join(emergency_keywords)})"
            query_params = {
                'senderId': sender_id,
                'note': note_text
            }
            api_url_with_params = f"{api_url}?{urllib.parse.urlencode(query_params)}"
            
            # multipart/form-data 형식으로 전송 (image는 빈 값)
            files = {
                'image': ('', '')  # 빈 이미지 파일
            }
            
            logger.info(f"📤 API 요청 URL: {api_url_with_params}")
            logger.info(f"📤 Multipart files: {files}")

            # ✅ 수정: requests.post() 사용
            response = requests.post(
                url=api_url_with_params,
                files=files,
                timeout=10
            )
            
            logger.info(f"✅ API 호출 성공 (Status: {response.status_code})")
            logger.info(f"   - Response: {response.text[:200]}")
    
    except requests.exceptions.Timeout:
        logger.error("❌ API 호출 타임아웃")
    
    except requests.exceptions.ConnectionError:
        logger.error("❌ API 연결 오류")
    
    except Exception as e:
        logger.error(f"❌ API 호출 중 오류 발생: {e}", exc_info=True)

# 언어 매핑
LANGUAGE_MAP = {
    "자동 감지": "auto",
    "한국어": "ko",
    "중국어": "zh",
    "영어": "en",
    "일본어": "ja",
    "광동어": "yue",
}

# ====================
# 정답 데이터 (Ground Truth)
# ====================
GROUND_TRUTHS = [
    # 일상 상황 10개
    "회의는 오후 세 시에 시작해 알림 설정해 줘",
    "내일 아침 일곱 시에 기상 알람을 추가해",
    "거실 불 끄고 공기청정기 약하게 켜",
    "오늘 점심은 김치볶음밥 두 개 주문할까",
    "블루투스 이어폰 배터리 잔량 얼마야",
    "일정에 고객 미팅 오후 두 시로 등록해",
    "와이파이가 자꾸 끊겨 속도 테스트 해봐",
    "영수증 사진을 스캔해서 이메일로 보내",
    "주말에 가족 영화 추천해 줘 액션 말고",
    "날씨 어때 우산 챙겨야 할까",
    # 응급 상황 10개
    "도와줘 사람이 쓰러졌어",
    "119에 바로 신고해 호흡이 멈춘 것 같아",
    "불이야 주방에서 연기가 나",
    "심장이 아파 가슴이 조여 와",
    "큰 사고야 피가 많이 나 위치 전송해 줘",
    "알러지 반응이야 숨쉬기 힘들어.",
    "어지럽고 구토가 나 구급차 호출해",
    "노약자가 계단에서 넘어졌어 의식이 희미해",
    "가스 냄새가 심해 즉시 환기하고 신고해",
    "아이 체온이 40도야 응급실 안내해 줘",
]

LABELS = ["일상"] * 10 + ["응급"] * 10


# ====================
# 🔹 세션 결과 저장소 (마이크 실시간 음성인식용)
# ====================
class MicrophoneSessionRecorder:
    """마이크 실시간 음성인식 세션 결과를 누적 저장하는 클래스"""

    def __init__(self):
        self.sessions = []  # 각 세션의 결과를 저장
        self.current_session_id = 0
        self.lock = threading.Lock()

    def add_session_result(self, ground_truth: str, asr_result: str, duration: float, timestamp: str):
        """세션 결과 추가"""
        with self.lock:
            self.current_session_id += 1
            session_data = {
                "session_id": self.current_session_id,
                "timestamp": timestamp,
                "duration": duration,
                "ground_truth": ground_truth,
                "asr_result": asr_result,
            }
            self.sessions.append(session_data)
            logger.info(f"✅ 세션 결과 저장 완료: Session #{self.current_session_id}")

    def get_all_sessions(self) -> List[Dict]:
        """모든 세션 결과 반환"""
        with self.lock:
            return self.sessions.copy()

    def get_session_count(self) -> int:
        """저장된 세션 개수 반환"""
        with self.lock:
            return len(self.sessions)

    def clear_sessions(self):
        """모든 세션 결과 초기화"""
        with self.lock:
            self.sessions.clear()
            self.current_session_id = 0
            logger.info("🔄 세션 결과 초기화 완료")


# 전역 세션 레코더
mic_session_recorder = MicrophoneSessionRecorder()

# 🔹 VAD 세션 채팅 히스토리 (실시간 누적 표시용)
vad_chat_history = []


def clear_vad_chat_history():
    """VAD 채팅 히스토리 초기화"""
    global vad_chat_history
    vad_chat_history = []
    logger.info("🗑️ VAD 채팅 히스토리 초기화")


def add_to_vad_chat_history(timestamp: str, text: str, duration: float, is_emergency: bool = False, emergency_keywords: list = None):
    """VAD 채팅 히스토리에 메시지 추가"""
    global vad_chat_history
    
    message = {
        'timestamp': timestamp,
        'text': text,
        'duration': duration,
        'is_emergency': is_emergency,
        'emergency_keywords': emergency_keywords or []
    }
    
    vad_chat_history.append(message)
    logger.debug(f"📝 채팅 히스토리 추가: {len(vad_chat_history)}개")


def format_vad_chat_history() -> str:
    """VAD 채팅 히스토리를 포맷팅하여 문자열로 반환"""
    global vad_chat_history
    
    if not vad_chat_history:
        return "👂 대기 중... 말씀해주세요."
    
    formatted = "🔴 음성인식 세션 활성화 중...\n\n"
    formatted += f"📊 감지된 음성 구간: {len(vad_chat_history)}개\n\n"
    formatted += "=" * 60 + "\n\n"
    
    for idx, msg in enumerate(vad_chat_history, 1):
        timestamp = msg['timestamp']
        text = msg['text']
        duration = msg['duration']
        is_emergency = msg['is_emergency']
        emergency_keywords = msg['emergency_keywords']
        
        # 구간 번호와 시간 표시
        formatted += f"[{idx}] {timestamp} ({duration:.1f}초)\n"
        
        # 응급 상황 표시
        if is_emergency:
            formatted += f"🚨 응급: {text}\n"
            formatted += f"   키워드: {', '.join(emergency_keywords)}\n"
        else:
            formatted += f"💬 {text}\n"
        
        formatted += "\n"
    
    formatted += "=" * 60 + "\n"
    formatted += "👂 계속 듣고 있습니다. 말씀해주세요..."
    
    return formatted


# ====================
# 🔹 CSV 리포트 생성 함수
# ====================
def generate_mic_session_csv_report(
    sessions: List[Dict],
    matcher,  # SpeechRecognitionMatcher 객체
    output_csv_path: str = None
) -> str:
    """
    마이크 실시간 음성인식 세션 결과에 대한 CSV 리포트 생성

    Args:
        sessions: 세션 결과 리스트 (각 dict는 session_id, timestamp, duration, ground_truth, asr_result 포함)
        matcher: SpeechRecognitionMatcher 객체
        output_csv_path: 저장될 CSV 경로 (None이면 자동 생성)

    Returns:
        생성된 CSV 파일 경로
    """

    if not sessions:
        logger.warning("⚠️ 생성할 세션 결과가 없습니다.")
        return None

    # 자동 파일명 생성
    if output_csv_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv_path = f"mic_session_cer_report_{timestamp}.csv"

    rows = []

    for session in sessions:
        session_id = session.get("session_id", "N/A")
        timestamp = session.get("timestamp", "N/A")
        duration = session.get("duration", 0.0)
        gt = session.get("ground_truth", "")
        asr = session.get("asr_result", "")

        # CER 직접 계산
        cer_direct = matcher.cer_direct(asr, gt)

        # jiwer CER 계산
        cer_jiwer_data = matcher.cer_jiwer(asr, gt)

        row = {
            "session_id": session_id,
            "timestamp": timestamp,
            "duration_sec": f"{duration:.2f}",
            "ground_truth": gt,
            "asr": asr,

            # 직접 CER
            "cer_direct": f"{cer_direct['CER']:.4f}",
            "S_direct": cer_direct["S"],
            "D_direct": cer_direct["D"],
            "I_direct": cer_direct["I"],
            "N_direct": cer_direct["N"],
        }

        # jiwer CER 존재 여부 체크
        if cer_jiwer_data:
            row.update({
                "cer_jiwer": f"{cer_jiwer_data['CER']:.4f}",
                "S_jiwer": cer_jiwer_data["S"],
                "D_jiwer": cer_jiwer_data["D"],
                "I_jiwer": cer_jiwer_data["I"],
                "N_jiwer": cer_jiwer_data["N"],
            })
        else:
            row.update({
                "cer_jiwer": "",
                "S_jiwer": "",
                "D_jiwer": "",
                "I_jiwer": "",
                "N_jiwer": "",
            })

        rows.append(row)

    # CSV 저장
    header = [
        "session_id", "timestamp", "duration_sec", "ground_truth", "asr",
        "cer_direct", "S_direct", "D_direct", "I_direct", "N_direct",
        "cer_jiwer",  "S_jiwer", "D_jiwer", "I_jiwer", "N_jiwer"
    ]

    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"[✔] 마이크 세션 CSV 리포트 생성 완료 → {output_csv_path}")
    return output_csv_path


def generate_batch_csv_report(
    file_names: List[str],
    ground_truths: List[str],
    asr_results: List[str],
    matcher,  # SpeechRecognitionMatcher 객체
    output_csv_path: str = None
) -> str:
    """
    배치 파일 음성 인식 결과에 대한 CSV 리포트 생성

    Args:
        file_names: 파일명 리스트
        ground_truths: 정답(GT) 리스트
        asr_results: ASR 인식 결과 리스트
        matcher: SpeechRecognitionMatcher 객체
        output_csv_path: 저장될 CSV 경로 (None이면 자동 생성)

    Returns:
        생성된 CSV 파일 경로
    """

    assert len(ground_truths) == len(asr_results), "GT와 ASR 개수가 다릅니다."
    if len(file_names) != len(ground_truths):
        # 길이가 다르면 자동 번호 생성
        file_names = [f"audio_{i+1}.wav" for i in range(len(ground_truths))]

    # 자동 파일명 생성
    if output_csv_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv_path = f"batch_cer_report_{timestamp}.csv"

    rows = []

    for idx, (fname, gt, asr) in enumerate(zip(file_names, ground_truths, asr_results)):
        # CER 직접 계산
        cer_direct = matcher.cer_direct(asr, gt)

        # jiwer CER 계산
        cer_jiwer_data = matcher.cer_jiwer(asr, gt)

        row = {
            "file_name": fname,
            "ground_truth": gt,
            "asr": asr,

            # 직접 CER
            "cer_direct": f"{cer_direct['CER']:.4f}",
            "S_direct": cer_direct["S"],
            "D_direct": cer_direct["D"],
            "I_direct": cer_direct["I"],
            "N_direct": cer_direct["N"],
        }

        # jiwer CER 존재 여부 체크
        if cer_jiwer_data:
            row.update({
                "cer_jiwer": f"{cer_jiwer_data['CER']:.4f}",
                "S_jiwer": cer_jiwer_data["S"],
                "D_jiwer": cer_jiwer_data["D"],
                "I_jiwer": cer_jiwer_data["I"],
                "N_jiwer": cer_jiwer_data["N"],
            })
        else:
            row.update({
                "cer_jiwer": "",
                "S_jiwer": "",
                "D_jiwer": "",
                "I_jiwer": "",
                "N_jiwer": "",
            })

        rows.append(row)

    # CSV 저장
    header = [
        "file_name", "ground_truth", "asr",
        "cer_direct", "S_direct", "D_direct", "I_direct", "N_direct",
        "cer_jiwer",  "S_jiwer", "D_jiwer", "I_jiwer", "N_jiwer"
    ]

    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"[✔] 배치 CSV 리포트 생성 완료 → {output_csv_path}")
    return output_csv_path


# ====================
# 매칭 시스템
# ====================
class SpeechRecognitionMatcher:
    """음성인식 결과와 정답 문장을 비교하는 클래스"""

    EMERGENCY_KEYWORDS = [
        "도와줘", "살려줘", "119", "응급", "불이야", "화재",
        "심장", "호흡", "출혈", "사고", "구급차", "응급실",
        "알러지", "구토", "의식", "가스",
    ]

    def __init__(self, ground_truths: List[str], labels: List[str] = None):
        self.ground_truths = ground_truths
        self.labels = labels if labels else ["일상"] * len(ground_truths)
        self.evaluation_results = []

    def preprocess(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        return SequenceMatcher(None, text1, text2).ratio()

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def character_accuracy(self, recognized: str, ground_truth: str) -> float:
        recognized = self.preprocess(recognized)
        ground_truth = self.preprocess(ground_truth)
        lev_dist = self.levenshtein_distance(recognized, ground_truth)
        max_len = max(len(recognized), len(ground_truth))
        if max_len == 0:
            return 1.0
        accuracy = 1.0 - (lev_dist / max_len)
        return max(0.0, accuracy)

    def detect_emergency_keywords(self, text: str) -> List[str]:
        detected = []
        text = self.preprocess(text)
        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in text:
                detected.append(keyword)
        return detected

    def find_best_match(self, recognized_text: str) -> Dict:
        recognized_text = self.preprocess(recognized_text)
        best_match = ""
        best_similarity = 0.0
        best_index = -1
        best_accuracy = 0.0

        for idx, ground_truth in enumerate(self.ground_truths):
            gt = self.preprocess(ground_truth)
            similarity = self.calculate_similarity(recognized_text, gt)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = ground_truth
                best_index = idx
                best_accuracy = self.character_accuracy(recognized_text, ground_truth)

        emergency_keywords = self.detect_emergency_keywords(recognized_text)
        is_emergency = len(emergency_keywords) > 0


        # 🔹 best_match에 대해 CER 계산
        cer_direct = None
        cer_jiwer_result = None
        if best_match:
            cer_direct = self.cer_direct(recognized_text, best_match)
            cer_jiwer_result = self.cer_jiwer(recognized_text, best_match)

        result = {
            "recognized": recognized_text,
            "best_match": best_match,
            "similarity": best_similarity,
            "accuracy": best_accuracy,
            "index": best_index,
            "label": self.labels[best_index] if best_index >= 0 else "unknown",
            "emergency_keywords": emergency_keywords,
            "is_emergency": is_emergency,
            # 🔹 추가된 필드들
            "cer": cer_direct["CER"] if cer_direct else None,  # CER 값만 표시 (0.xx 형식)
            "cer_direct": cer_direct,         # 전체 정보 (S, D, I, N 포함)
            "cer_jiwer": cer_jiwer_result["CER"] if cer_jiwer_result else None,  # jiwer CER 값만
            "cer_jiwer_full": cer_jiwer_result,    # jiwer 기반 전체 결과 (또는 None)
        }
        self.evaluation_results.append(result)
        return result


    def reset_evaluation(self):
        self.evaluation_results = []

    # ============================
    # 🔹 (A) 직접 구현한 CER 계산
    # ============================
    def cer_direct(
        self,
        recognized: str,
        ground_truth: str,
        ignore_spaces: bool = True,
    ) -> Dict[str, float]:
        """
        직접 구현한 Levenshtein DP + traceback으로 CER 계산
        CER = (S + D + I) / N
          - N: 정답(GT) 전체 음절 수
          - S: 치환(substitution) 개수
          - D: 삭제(deletion) 개수
          - I: 삽입(insertion) 개수
        """

        # 전처리
        rec = self.preprocess(recognized)
        gt = self.preprocess(ground_truth)

        if ignore_spaces:
            rec = rec.replace(" ", "")
            gt = gt.replace(" ", "")

        ref_chars = list(gt)   # 정답(GT)
        hyp_chars = list(rec)  # 인식 결과

        r = len(ref_chars)
        h = len(hyp_chars)

        # DP 테이블 생성
        dp = [[0] * (h + 1) for _ in range(r + 1)]
        for i in range(r + 1):
            dp[i][0] = i   # 삭제
        for j in range(h + 1):
            dp[0][j] = j   # 삽입

        # DP 채우기
        for i in range(1, r + 1):
            for j in range(1, h + 1):
                cost = 0 if ref_chars[i - 1] == hyp_chars[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,      # 삭제 D
                    dp[i][j - 1] + 1,      # 삽입 I
                    dp[i - 1][j - 1] + cost,  # 치환 S or 일치(hit)
                )

        # traceback 으로 S, D, I 계산
        i, j = r, h
        S = D = I = 0

        while i > 0 or j > 0:
            # 삭제
            if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
                D += 1
                i -= 1
            # 삽입
            elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
                I += 1
                j -= 1
            else:
                # 대각선 이동: 치환 또는 일치
                if i > 0 and j > 0 and ref_chars[i - 1] != hyp_chars[j - 1]:
                    S += 1
                i -= 1
                j -= 1

        N = r  # 정답 길이
        cer = (S + D + I) / N if N > 0 else 0.0

        return {
            "CER": cer,
            "S": S,
            "D": D,
            "I": I,
            "N": N,
        }

    # ============================
    # 🔹 (B) jiwer 기반 CER 계산
    # ============================
    def cer_jiwer(
        self,
        recognized: str,
        ground_truth: str,
        ignore_spaces: bool = True,
    ) -> Optional[Dict[str, float]]:
        """
        jiwer 라이브러리를 이용한 CER 계산
        (jiwer가 설치되어 있지 않으면 None 반환)
        """

        if not JIWER_AVAILABLE:
            # jiwer 미설치 시에는 None 반환 (또는 예외 발생시켜도 됨)
            logging.warning(
                "jiwer 라이브러리가 설치되어 있지 않습니다. `pip install jiwer` 후 사용하세요."
            )
            return None

        def char_transform(s: str):
            s = self.preprocess(s)
            if ignore_spaces:
                s = s.replace(" ", "")
            return list(s)

        measures = compute_measures(
            truth=ground_truth,
            hypothesis=recognized,
            truth_transform=char_transform,
            hypothesis_transform=char_transform,
        )

        S = measures["substitutions"]
        D = measures["deletions"]
        I = measures["insertions"]
        N = measures["reference_length"]
        cer = (S + D + I) / N if N > 0 else 0.0

        return {
            "CER": cer,
            "S": S,
            "D": D,
            "I": I,
            "N": N,
            "raw_measures": measures,
        }


matcher = SpeechRecognitionMatcher(GROUND_TRUTHS, LABELS)


# ====================
# Streaming Processor with VAD (Voice Activity Detection)
# ====================
class VADStreamingProcessor:
    """에너지 기반 간단한 VAD를 사용한 실시간 음성인식 프로세서"""

    def __init__(self, recognizer, sample_rate=16000, vad_enabled=True):
        self.recognizer = recognizer
        self.sample_rate = sample_rate
        
        # 간단한 에너지 기반 VAD 설정
        self.vad_enabled = vad_enabled
        self.energy_threshold = 0.01  # 에너지 임계값 (조정 가능)
        self.silence_duration = 1.5  # 침묵 판단 시간 (초)
        self.min_speech_duration = 0.5  # 최소 음성 길이 (초)
        
        # 음성 버퍼
        self.audio_buffer = deque()
        self.speech_segments = []  # 음성 구간 저장
        
        # 상태 관리
        self.is_session_active = False  # 세션 활성화 상태
        self.is_processing = False  # 음성 처리 중
        self.silence_frames = 0  # 침묵 프레임 카운터
        self.speech_frames = 0  # 음성 프레임 카운터
        self.last_result = ""
        self.lock = threading.Lock()
        
        logger.info(f"✅ VADStreamingProcessor 초기화 완료")
        logger.info(f"   - VAD: 에너지 기반 간단한 VAD")
        logger.info(f"   - 에너지 임계값: {self.energy_threshold}")
        logger.info(f"   - 침묵 감지: {self.silence_duration}초")

    def _calculate_energy(self, audio_chunk: np.ndarray) -> float:
        """오디오 청크의 에너지 계산 (RMS)"""
        return np.sqrt(np.mean(audio_chunk ** 2))

    def _is_speech(self, audio_chunk: np.ndarray) -> bool:
        """에너지 기반 음성 감지"""
        if not self.vad_enabled:
            return True
        
        energy = self._calculate_energy(audio_chunk)
        return energy > self.energy_threshold

    def start_session(self):
        """음성인식 세션 시작 (마이크 계속 켜짐)"""
        with self.lock:
            if self.is_session_active:
                logger.warning("⚠️ 이미 세션이 활성화되어 있습니다.")
                return False
            
            self.is_session_active = True
            self.is_processing = False
            self.audio_buffer.clear()
            self.speech_segments.clear()
            self.last_result = ""
            self.silence_frames = 0
            self.speech_frames = 0
            
            logger.info("=" * 60)
            logger.info("🎤 음성인식 세션 시작")
            logger.info("   - 마이크 활성화: 계속 듣기 모드")
            logger.info("   - 에너지 기반 VAD로 음성 자동 감지")
            logger.info("=" * 60)
            return True

    def stop_session(self):
        """음성인식 세션 종료 (마이크 끔)"""
        with self.lock:
            if not self.is_session_active:
                logger.warning("⚠️ 활성화된 세션이 없습니다.")
                return None
            
            logger.info("⏹️ 음성인식 세션 종료 요청")
            
            # 남은 버퍼가 있으면 처리
            if len(self.audio_buffer) > 0 and self.is_processing:
                speech_audio = np.array(self.audio_buffer)
                duration = len(speech_audio) / self.sample_rate
                
                if duration >= self.min_speech_duration:
                    result = self._process_speech_segment(speech_audio)
                    if result:
                        self.speech_segments.append(result)
            
            self.is_session_active = False
            self.is_processing = False
            
            # 세션 통계
            segment_count = len(self.speech_segments)
            total_duration = sum(seg.get('duration', 0) for seg in self.speech_segments)
            
            logger.info(f"📊 세션 통계:")
            logger.info(f"   - 감지된 음성 구간: {segment_count}개")
            logger.info(f"   - 총 음성 길이: {total_duration:.1f}초")
            
            result = {
                'segments': self.speech_segments.copy(),
                'total_segments': segment_count,
                'total_duration': total_duration
            }
            
            self.audio_buffer.clear()
            self.speech_segments.clear()
            self.silence_frames = 0
            self.speech_frames = 0
            
            return result

    def add_audio_chunk(self, audio_chunk: np.ndarray) -> Optional[Dict]:
        """
        오디오 청크 추가 및 VAD 기반 처리
        
        Returns:
            음성 감지 및 인식 결과 딕셔너리 또는 None
        """
        with self.lock:
            if not self.is_session_active:
                return None
            
            try:
                # 음성 활동 감지
                is_speech = self._is_speech(audio_chunk)
                
                if is_speech:
                    # 음성이 감지되면
                    self.silence_frames = 0
                    self.speech_frames += 1
                    
                    if not self.is_processing:
                        # 새로운 음성 구간 시작
                        self.is_processing = True
                        self.audio_buffer.clear()
                        logger.info("🗣️ 음성 감지 시작")
                    
                    self.audio_buffer.extend(audio_chunk)
                else:
                    # 침묵이 감지되면
                    self.silence_frames += 1
                    
                    if self.is_processing:
                        # 음성 처리 중인 경우 버퍼에 추가 (짧은 침묵 포함)
                        self.audio_buffer.extend(audio_chunk)
                        
                        # 침묵 시간 계산
                        silence_duration = (self.silence_frames * len(audio_chunk)) / self.sample_rate
                        
                        # 충분한 침묵이 감지되면 음성 구간 처리
                        if silence_duration >= self.silence_duration:
                            speech_audio = np.array(self.audio_buffer)
                            duration = len(speech_audio) / self.sample_rate
                            
                            if duration >= self.min_speech_duration:
                                result = self._process_speech_segment(speech_audio)
                                
                                if result:
                                    logger.info(f"✅ 음성 처리 완료 ({duration:.1f}초)")
                                    self.speech_segments.append(result)
                                    self.is_processing = False
                                    self.audio_buffer.clear()
                                    self.silence_frames = 0
                                    self.speech_frames = 0
                                    return result
                            else:
                                logger.debug(f"⏭️ 너무 짧은 음성 무시 ({duration:.1f}초)")
                            
                            self.is_processing = False
                            self.audio_buffer.clear()
                            self.silence_frames = 0
                            self.speech_frames = 0
                
            except Exception as e:
                logger.error(f"❌ 오디오 처리 중 오류: {e}", exc_info=True)
                return None
        
        return None

    def _process_speech_segment(self, audio_data: np.ndarray) -> Optional[Dict]:
        """음성 구간 처리 및 인식"""
        try:
            duration = len(audio_data) / self.sample_rate
            
            # 음성인식 수행
            stream = self.recognizer.create_stream()
            stream.accept_waveform(self.sample_rate, audio_data)
            self.recognizer.decode_stream(stream)
            result = stream.result
            
            text = result.text.strip()
            
            if text:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                segment_result = {
                    'timestamp': timestamp,
                    'text': text,
                    'duration': duration,
                    'confidence': 1.0  # Sherpa-ONNX는 confidence score를 제공하지 않음
                }
                
                logger.info(f"📝 인식 결과: {text}")
                self.last_result = text
                
                return segment_result
            else:
                logger.debug("🔇 인식된 텍스트 없음")
                return None
        
        except Exception as e:
            logger.error(f"❌ 음성 인식 오류: {e}", exc_info=True)
            return None

    def get_session_status(self) -> Dict:
        """현재 세션 상태 반환"""
        with self.lock:
            return {
                'is_active': self.is_session_active,
                'is_processing': self.is_processing,
                'segments_count': len(self.speech_segments),
                'last_result': self.last_result
            }

    def reset(self):
        """완전 초기화"""
        with self.lock:
            logger.info("🔄 VADStreamingProcessor 초기화")
            self.is_session_active = False
            self.is_processing = False
            self.audio_buffer.clear()
            self.speech_segments.clear()
            self.last_result = ""
            self.silence_frames = 0
            self.speech_frames = 0


# 기존 StreamingProcessor는 하위 호환성을 위해 유지
class StreamingProcessor:
    """Offline Recognizer를 사용한 청크 기반 스트리밍 처리 (레거시)"""

    def __init__(self, recognizer, sample_rate=16000, chunk_duration=20.0):
        self.recognizer = recognizer
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)

        self.audio_buffer = deque()
        self.is_recording = False
        self.is_ready = False
        self.accumulated_audio = []
        self.last_result = ""
        self.lock = threading.Lock()

        logger.info(f"✅ StreamingProcessor 초기화 (청크 크기: {chunk_duration}초)")
        logger.debug(f"초기 상태: is_ready={self.is_ready}, is_recording={self.is_recording}")

    def prepare(self):
        """녹음 준비 (is_recording은 False 유지)"""
        with self.lock:
            old_state = (self.is_ready, self.is_recording)

            self.is_ready = True
            self.is_recording = False
            self.audio_buffer.clear()
            self.accumulated_audio.clear()
            self.last_result = ""

            new_state = (self.is_ready, self.is_recording)

            logger.info("=" * 60)
            logger.info("🟡 녹음 준비 완료")
            logger.debug(f"상태 변경: {old_state} → {new_state}")
            logger.debug(f"버퍼 초기화 완료")
            logger.info("=" * 60)

    def start_recording(self):
        """녹음 시작 (마이크 활성화 시 호출)"""
        with self.lock:
            if not self.is_ready:
                logger.warning("⚠️ 준비되지 않은 상태에서 녹음 시작 시도")
                logger.debug(f"현재 상태: is_ready={self.is_ready}, is_recording={self.is_recording}")
                return False

            old_state = self.is_recording
            self.is_recording = True

            logger.info("=" * 60)
            logger.info("🔴 녹음 시작")
            logger.debug(f"is_recording: {old_state} → {self.is_recording}")
            logger.info("=" * 60)
            return True

    def stop_recording(self):
        """녹음 종료 및 최종 처리"""
        with self.lock:
            logger.info("⏹️ 녹음 종료 요청")
            logger.debug(f"현재 상태: is_ready={self.is_ready}, is_recording={self.is_recording}")

            if not self.is_recording:
                logger.warning("녹음 중이 아닌 상태에서 종료 요청")
                return None

            self.is_recording = False
            self.is_ready = False

            logger.debug(f"상태 변경: is_recording={True} → {False}, is_ready={True} → {False}")

            # 남은 버퍼 처리
            if len(self.accumulated_audio) > 0:
                final_audio = np.concatenate(self.accumulated_audio)
                duration = len(final_audio) / self.sample_rate
                logger.info(f"최종 오디오 처리: {duration:.2f}초")

                result = self._process_audio(final_audio)
                logger.info(f"⏹️ 녹음 종료 - 최종 길이: {duration:.2f}초")
                return result

            logger.warning("누적된 오디오가 없음")
            return self.last_result

    def add_audio_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        """오디오 청크 추가 및 처리"""
        # 🔧 스레드 안전성 개선: 락 범위 최적화
        with self.lock:
            # is_ready이면서 is_recording=False인 경우: 첫 오디오 도착 시 자동 시작
            if self.is_ready and not self.is_recording:
                self.is_recording = True
                logger.info("🎤 마이크 활성화 감지 → 자동 녹음 시작")
                logger.debug(f"is_recording: False → True (자동 전환)")

            if not self.is_recording:
                logger.debug(f"녹음 중이 아니므로 오디오 청크 무시 (is_ready={self.is_ready})")
                return None

            try:
                # 버퍼에 추가
                chunk_len = len(audio_chunk)
                self.audio_buffer.extend(audio_chunk)
                self.accumulated_audio.append(audio_chunk)

                logger.debug(f"오디오 청크 추가: {chunk_len} samples, 누적: {len(self.accumulated_audio)} chunks")

                # 청크 크기 충족 시 처리
                if len(self.audio_buffer) >= self.chunk_size:
                    logger.debug(f"청크 크기 도달: {len(self.audio_buffer)} >= {self.chunk_size}")

                    # 전체 누적 오디오로 처리 (더 나은 컨텍스트)
                    full_audio = np.concatenate(self.accumulated_audio)
                    result = self._process_audio(full_audio)

                    # 버퍼 일부만 유지 (overlap)
                    overlap_size = self.chunk_size // 4
                    self.audio_buffer = deque(list(self.audio_buffer)[self.chunk_size - overlap_size:])

                    logger.debug(f"버퍼 업데이트: overlap={overlap_size}, 남은 버퍼={len(self.audio_buffer)}")

                    if result and result != self.last_result:
                        self.last_result = result
                        logger.info(f"새로운 인식 결과: {result[:50]}...")
                        return result

            except Exception as e:
                logger.error(f"❌ 오디오 청크 처리 중 오류: {e}", exc_info=True)
                # 예외 발생 시에도 상태 일관성 유지
                return None

        return None

    def _process_audio(self, audio_data: np.ndarray) -> str:
        """오디오 데이터 처리"""
        try:
            duration = len(audio_data) / self.sample_rate
            logger.debug(f"음성인식 처리 시작: {duration:.2f}초")

            if duration < 0.5:
                logger.debug("오디오 길이가 0.5초 미만, 처리 건너뜀")
                return ""

            # Offline Recognizer로 처리
            stream = self.recognizer.create_stream()
            stream.accept_waveform(self.sample_rate, audio_data)
            self.recognizer.decode_stream(stream)
            result = stream.result

            text = result.text.strip()
            logger.debug(f"음성인식 결과: '{text}'")
            return text

        except Exception as e:
            logger.error(f"❌ 오디오 처리 오류: {e}", exc_info=True)
            return ""

    def get_current_duration(self) -> float:
        """현재 녹음 길이 반환"""
        if len(self.accumulated_audio) > 0:
            total_samples = sum(len(chunk) for chunk in self.accumulated_audio)
            duration = total_samples / self.sample_rate
            logger.debug(f"현재 녹음 길이: {duration:.2f}초 ({len(self.accumulated_audio)} chunks)")
            return duration
        return 0.0

    def reset(self):
        """완전 초기화"""
        with self.lock:
            logger.info("🔄 StreamingProcessor 완전 초기화")
            logger.debug(f"초기화 전 상태: is_ready={self.is_ready}, is_recording={self.is_recording}")

            self.is_recording = False
            self.is_ready = False
            self.audio_buffer.clear()
            self.accumulated_audio.clear()
            self.last_result = ""

            logger.debug("초기화 완료: is_ready=False, is_recording=False, 버퍼 비움")


# 전역 스트림 프로세서 (VAD 기반)
vad_stream_processor: Optional[VADStreamingProcessor] = None
stream_processor: Optional[StreamingProcessor] = None


# ====================
# 모델 로딩
# ====================
def load_model():
    """Offline Recognizer 로드"""
    global recognizer, vad_stream_processor

    logger.info("=" * 60)
    logger.info("🔄 Sherpa-ONNX Sense-Voice RKNN 모델 로딩 중...")
    logger.info("📦 모델: sense-voice (zh, en, ja, ko, yue)")
    logger.info("🖥️ 플랫폼: RK3588 - NPU 최적화")
    logger.info("=" * 60)

    if not os.path.exists(MODEL_DIR):
        raise FileNotFoundError(f"모델 디렉토리 없음: {MODEL_DIR}")

    required_files = {
        "RKNN Model": MODEL_PATH,
        "Tokens": TOKENS_PATH,
    }

    logger.info("📁 모델 파일 확인:")
    for name, path in required_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024**2)
            logger.info(f"  ✅ {name}: {os.path.basename(path)} ({size:.2f} MB)")
        else:
            raise FileNotFoundError(f"필수 파일 없음: {name}")

    logger.info("⚙️ Offline Recognizer 초기화 중...")
    try:
        recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=MODEL_PATH,
            tokens=TOKENS_PATH,
            num_threads=4,
            provider="rknn",
            use_itn=True,
            debug=False,
        )
        logger.info("✅ Offline Recognizer 로딩 완료!")

        # 🔧 VAD 기반 스트림 프로세서 생성
        vad_stream_processor = VADStreamingProcessor(
            recognizer, 
            sample_rate=16000,
            vad_enabled=True  # VAD 활성화
        )
        logger.info("✅ VADStreamingProcessor 생성 완료 (VAD 지원)")

    except Exception as e:
        logger.error(f"❌ Recognizer 로딩 실패: {e}", exc_info=True)
        raise

    logger.info("=" * 60)
    logger.info("✅ 모델 로딩 완료!")
    logger.info("=" * 60)


# ====================
# 오디오 처리 함수
# ====================
def resample_audio(audio_data, orig_sr, target_sr=16000):
    """오디오 리샘플링"""
    if orig_sr == target_sr:
        return audio_data

    try:
        import librosa
        return librosa.resample(audio_data, orig_sr=orig_sr, target_sr=target_sr)
    except ImportError:
        from scipy import signal
        num_samples = int(len(audio_data) * target_sr / orig_sr)
        return signal.resample(audio_data, num_samples)


def read_wave(wave_filename: str):
    """Wave 파일 읽기"""
    with wave.open(wave_filename) as f:
        if f.getnchannels() != 1:
            raise ValueError(f"모노 오디오만 지원. 채널: {f.getnchannels()}")
        if f.getsampwidth() != 2:
            raise ValueError(f"16비트 오디오만 지원. 샘플폭: {f.getsampwidth()}")

        num_samples = f.getnframes()
        samples = f.readframes(num_samples)
        samples_int16 = np.frombuffer(samples, dtype=np.int16)
        samples_float32 = samples_int16.astype(np.float32) / 32768.0
        return samples_float32, f.getframerate()


# ====================
# 🔹 마이크 세션 관련 핸들러 함수 (VAD 기반)
# ====================
def start_vad_session_handler():
    """
    음성인식 세션 시작 핸들러 (VAD 기반)
    
    - 마이크 계속 켜짐
    - VAD로 음성 자동 감지
    - 음성 감지 시 자동으로 ASR-STT 수행
    """
    global vad_stream_processor

    logger.info("=" * 60)
    logger.info("🎤 음성인식 세션 시작 요청")

    if vad_stream_processor is None:
        logger.error("VADStreamingProcessor가 초기화되지 않음")
        return [
            gr.update(interactive=True, value="🎙️ 음성인식 시작"),
            gr.update(interactive=False),
            None,
            "❌ 오류: 음성인식 시스템이 초기화되지 않았습니다."
        ]
    
    # 세션 시작
    success = vad_stream_processor.start_session()
    
    if success:
        session_count = mic_session_recorder.get_session_count()
        status_msg = (
            "🎤 음성인식 세션 활성화!\n\n"
            "✅ 마이크가 계속 켜져 있습니다.\n"
            "✅ 말하기 시작하면 자동으로 인식됩니다.\n"
            "✅ VAD가 음성을 자동 감지합니다.\n\n"
            "🔴 음성인식 종료 버튼을 눌러 세션을 종료하세요.\n\n"
            f"📊 이전 저장된 세션: {session_count}개"
        )
        
        logger.info("✅ 음성인식 세션 시작 성공")
        logger.info("=" * 60)
        
        return [
            gr.update(interactive=False, value="🔴 음성인식 세션 활성화 중..."),
            gr.update(interactive=True),
            None,
            status_msg
        ]
    else:
        return [
            gr.update(interactive=True, value="🎙️ 음성인식 시작"),
            gr.update(interactive=False),
            None,
            "⚠️ 세션을 시작할 수 없습니다. 다시 시도해주세요."
        ]


def stop_vad_session_handler(ground_truth_input):
    """
    음성인식 세션 종료 핸들러 (VAD 기반)
    
    - 세션 종료
    - 감지된 모든 음성 구간 결과 표시
    """
    global vad_stream_processor

    logger.info("⏹️ 음성인식 세션 종료 요청")

    if vad_stream_processor is None:
        logger.error("VADStreamingProcessor가 None")
        return [
            "⚠️ 음성인식 세션이 없습니다.",
            ""
        ]

    # 세션 종료
    session_result = vad_stream_processor.stop_session()
    
    if session_result:
        segments = session_result.get('segments', [])
        total_segments = session_result.get('total_segments', 0)
        total_duration = session_result.get('total_duration', 0)
        
        # 각 구간에 대한 응급 상황 체크
        emergency_detected = False
        emergency_segments = []
        
        result_text = f"⏹️ 음성인식 세션 종료\n\n"
        result_text += f"📊 세션 통계:\n"
        result_text += f"   - 감지된 음성 구간: {total_segments}개\n"
        result_text += f"   - 총 음성 길이: {total_duration:.1f}초\n\n"
        
        if segments:
            result_text += "📝 인식 결과:\n"
            result_text += "=" * 60 + "\n\n"
            
            for idx, seg in enumerate(segments, 1):
                text = seg.get('text', '')
                timestamp = seg.get('timestamp', '')
                duration = seg.get('duration', 0)
                
                result_text += f"[{idx}] {timestamp} ({duration:.1f}초)\n"
                result_text += f"    {text}\n\n"
                
                # 🚨 응급 상황 체크
                match_result = matcher.find_best_match(text)
                if match_result.get("is_emergency", False):
                    emergency_detected = True
                    emergency_keywords = match_result.get("emergency_keywords", [])
                    emergency_segments.append({
                        'index': idx,
                        'text': text,
                        'keywords': emergency_keywords,
                        'timestamp': timestamp
                    })
                    
                    logger.warning(f"🚨 응급 상황 감지 [구간 {idx}]: {emergency_keywords}")
                    
                    # API 호출 (실시간에 이미 호출되었지만 다시 확인)
                    # send_emergency_alert(text, emergency_keywords)
        else:
            result_text += "⚠️ 인식된 음성이 없습니다.\n"
        
        # 응급 상황 요약
        if emergency_detected:
            result_text += "\n" + "=" * 60 + "\n"
            result_text += "🚨🚨🚨 응급 상황 감지됨! 🚨🚨🚨\n\n"
            for emerg in emergency_segments:
                result_text += f"[구간 {emerg['index']}] {emerg['timestamp']}\n"
                result_text += f"   키워드: {', '.join(emerg['keywords'])}\n"
                result_text += f"   내용: {emerg['text']}\n\n"
            result_text += "✅ 응급 알림이 전송되었습니다.\n"
        
        # 세션 결과 저장 (전체 텍스트 합침)
        if segments:
            combined_text = " ".join([seg.get('text', '') for seg in segments])
            gt = ground_truth_input.strip() if ground_truth_input else "(정답 미입력)"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            mic_session_recorder.add_session_result(
                ground_truth=gt,
                asr_result=combined_text,
                duration=total_duration,
                timestamp=timestamp
            )
        
        session_count = mic_session_recorder.get_session_count()
        result_text += f"\n📊 현재 저장된 세션: {session_count}개"
        
        # 채팅 히스토리 초기화
        clear_vad_chat_history()
        
        logger.info("✅ 음성인식 세션 종료 완료")
        
        return [
            result_text,
            ""  # ground_truth 초기화
        ]
    else:
        session_count = mic_session_recorder.get_session_count()
        clear_vad_chat_history()  # 히스토리 초기화
        
        return [
            f"⏹️ 세션 종료\n\n⚠️ 활성화된 세션이 없었습니다.\n\n📊 현재 저장된 세션: {session_count}개",
            ""
        ]


# 레거시 함수들 (하위 호환성)
def start_recording_handler():
    """
    녹음 시작 버튼 핸들러 (레거시)
    
    🔧 v4 개선:
    - 단일 인스턴스 재사용 (매번 생성하지 않음)
    - prepare()로 상태 초기화
    """
    global stream_processor

    logger.info("=" * 60)
    logger.info("🟡 녹음 시작 버튼 클릭")

    # 🔧 v4: 단일 인스턴스 재사용
    if stream_processor is not None:
        logger.debug("기존 StreamingProcessor 재사용")
        stream_processor.prepare()
    else:
        # 초기화되지 않은 경우에만 생성 (일반적으로 발생하지 않음)
        logger.warning("StreamingProcessor가 None, 새로 생성")
        stream_processor = StreamingProcessor(recognizer, chunk_duration=20.0)
        stream_processor.prepare()

    logger.info(f"✅ 녹음 준비 완료: is_ready={stream_processor.is_ready}, is_recording={stream_processor.is_recording}")
    logger.info("=" * 60)

    # 현재 저장된 세션 개수 표시
    session_count = mic_session_recorder.get_session_count()
    status_msg = f"🟡 준비 완료!\n\n마이크 버튼(🎤)을 눌러 녹음을 시작하세요.\n2초마다 실시간 인식됩니다.\n\n📊 현재 저장된 세션: {session_count}개"

    return [
        gr.update(interactive=False, value="🟡 준비 완료 - 마이크 버튼을 눌러주세요"),
        gr.update(interactive=True),
        None,  # Audio 컴포넌트 리셋
        status_msg
    ]


def stop_recording_handler(ground_truth_input):
    """
    녹음 종료 버튼 핸들러

    🔧 v4 개선:
    - 정답(Ground Truth) 입력 받아서 세션 결과 저장
    """
    global stream_processor

    logger.info("⏹️ 녹음 종료 버튼 클릭")

    if stream_processor is None:
        logger.error("StreamingProcessor가 None")
        return [
            gr.update(interactive=True, value="🎙️ 녹음 시작"),
            gr.update(interactive=False),
            "⚠️ 녹음 세션이 없습니다.",
            ""  # ground_truth 초기화
        ]

    logger.debug(f"종료 전 상태: is_ready={stream_processor.is_ready}, is_recording={stream_processor.is_recording}")

    # is_ready만 True이고 is_recording이 False인 경우 (마이크를 누르지 않은 경우)
    if stream_processor.is_ready and not stream_processor.is_recording:
        logger.warning("마이크 버튼을 누르지 않은 상태에서 종료")
        stream_processor.reset()
        session_count = mic_session_recorder.get_session_count()
        return [
            gr.update(interactive=True, value="🎙️ 녹음 시작"),
            gr.update(interactive=False),
            f"⚠️ 마이크 버튼을 누르지 않아 녹음되지 않았습니다.\n\n📊 현재 저장된 세션: {session_count}개",
            ""  # ground_truth 초기화
        ]

    # 정상 녹음 종료
    final_text = stream_processor.stop_recording()
    duration = stream_processor.get_current_duration()

    if final_text:
        # 🔹 세션 결과 저장
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gt = ground_truth_input.strip() if ground_truth_input else "(정답 미입력)"

        mic_session_recorder.add_session_result(
            ground_truth=gt,
            asr_result=final_text,
            duration=duration,
            timestamp=timestamp
        )

        match_result = matcher.find_best_match(final_text)
        logger.info(f"⏹️ 최종 결과 ({duration:.1f}초): {match_result}")

        # 🚨 응급 상황 감지 시 API 호출
        if match_result.get("is_emergency", False):
            emergency_keywords = match_result.get("emergency_keywords", [])
            logger.warning(f"🚨 응급 상황 감지됨! 키워드: {emergency_keywords}")
            send_emergency_alert(final_text, emergency_keywords)

        session_count = mic_session_recorder.get_session_count()

        return [
            gr.update(interactive=True, value="🎙️ 녹음 시작"),
            gr.update(interactive=False),
            f"⏹️ 녹음 종료 ({duration:.1f}초)\n\n✅ 최종 결과:\n{final_text}\n\n📊 현재 저장된 세션: {session_count}개",
            ""  # ground_truth 초기화
        ]
    else:
        logger.warning("인식된 텍스트 없음")
        session_count = mic_session_recorder.get_session_count()
        return [
            gr.update(interactive=True, value="🎙️ 녹음 시작"),
            gr.update(interactive=False),
            f"⏹️ 녹음 종료\n\n⚠️ 인식된 텍스트가 없습니다.\n\n📊 현재 저장된 세션: {session_count}개",
            ""  # ground_truth 초기화
        ]


def generate_mic_csv_handler():
    """마이크 세션 CSV 리포트 생성 핸들러"""
    sessions = mic_session_recorder.get_all_sessions()

    if not sessions:
        return None, "⚠️ 생성할 세션 결과가 없습니다. 먼저 녹음 테스트를 진행해주세요."

    # CSV 생성
    csv_path = generate_mic_session_csv_report(sessions, matcher)

    if csv_path and os.path.exists(csv_path):
        return csv_path, f"✅ CSV 리포트 생성 완료!\n\n📊 총 {len(sessions)}개 세션 처리\n📁 파일: {csv_path}"
    else:
        return None, "❌ CSV 리포트 생성 실패"


def clear_mic_sessions_handler():
    """마이크 세션 결과 초기화 핸들러"""
    mic_session_recorder.clear_sessions()
    return "✅ 모든 세션 결과가 초기화되었습니다.\n\n새로운 테스트를 시작하세요."


def auto_start_vad_session():
    """
    마이크 스트림 시작 시 자동으로 VAD 세션 활성화
    """
    global vad_stream_processor

    logger.info("🎤 마이크 활성화 감지 - 자동으로 VAD 세션 시작")

    if vad_stream_processor is None:
        logger.error("VADStreamingProcessor가 초기화되지 않음")
        return "❌ 오류: 음성인식 시스템이 초기화되지 않았습니다."
    
    # 기존 세션이 활성화되어 있으면 리셋
    if vad_stream_processor.get_session_status()['is_active']:
        vad_stream_processor.reset()
    
    # 채팅 히스토리 초기화
    clear_vad_chat_history()
    
    # 세션 시작
    success = vad_stream_processor.start_session()
    
    if success:
        session_count = mic_session_recorder.get_session_count()
        return (
            "🎤 음성인식 시작!\n\n"
            "✅ 마이크가 활성화되었습니다.\n"
            "✅ 말하기 시작하면 자동으로 인식됩니다.\n"
            "✅ VAD가 음성을 자동 감지합니다.\n\n"
            "🗣️ 지금 말씀해주세요...\n\n"
            f"📊 이전 저장된 세션: {session_count}개"
        )
    else:
        return "⚠️ 세션을 시작할 수 없습니다."


def reset_vad_session_handler():
    """
    VAD 세션 리셋 핸들러
    """
    global vad_stream_processor

    logger.info("🔄 VAD 세션 리셋 요청")

    if vad_stream_processor is None:
        return [
            None,
            "⚠️ 음성인식 시스템이 초기화되지 않았습니다.",
            ""
        ]
    
    vad_stream_processor.reset()
    clear_vad_chat_history()  # 채팅 히스토리 초기화
    session_count = mic_session_recorder.get_session_count()
    
    return [
        None,  # audio 컴포넌트 리셋
        f"🔄 세션이 초기화되었습니다.\n\n마이크 버튼을 다시 클릭하여 시작하세요.\n\n📊 저장된 세션: {session_count}개",
        ""  # ground_truth 초기화
    ]


def process_vad_audio_stream(audio_stream, language):
    """
    VAD 기반 마이크 스트리밍 오디오 처리
    
    - 자동으로 세션 시작
    - VAD로 음성 자동 감지
    - 음성 감지 시 자동 ASR-STT
    - 채팅 히스토리 누적 표시
    """
    global vad_stream_processor

    if audio_stream is None:
        yield ""
        return

    try:
        sr, audio_data = audio_stream

        if audio_data is None or len(audio_data) == 0:
            yield ""
            return

        # 스테레오 → 모노 변환
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # float32 정규화
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        elif audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # 16kHz 리샘플링
        if sr != 16000:
            audio_data = resample_audio(audio_data, sr, 16000)

        # 프로세서 확인
        if not vad_stream_processor:
            yield ""
            return

        # 세션이 활성화되지 않았으면 자동 시작
        status = vad_stream_processor.get_session_status()
        if not status['is_active']:
            logger.info("🎤 오디오 스트림 감지 - 자동으로 세션 시작")
            vad_stream_processor.start_session()
            clear_vad_chat_history()  # 히스토리 초기화
            
            session_count = mic_session_recorder.get_session_count()
            yield (
                "🎤 음성인식 자동 시작!\n\n"
                "✅ 말하기 시작하면 자동으로 인식됩니다.\n\n"
                "🗣️ 지금 말씀해주세요...\n\n"
                f"📊 저장된 세션: {session_count}개"
            )
            status = vad_stream_processor.get_session_status()

        # 오디오 청크 처리 (VAD 기반)
        result = vad_stream_processor.add_audio_chunk(audio_data)
        
        segments_count = status['segments_count']
        is_processing = status['is_processing']
        
        if result:
            # 새로운 음성 구간 인식 완료
            text = result.get('text', '')
            duration = result.get('duration', 0)
            timestamp = result.get('timestamp', '')
            
            # 🚨 응급 상황 실시간 체크
            match_result = matcher.find_best_match(text)
            is_emergency = False
            emergency_keywords = []
            
            if match_result.get("is_emergency", False):
                is_emergency = True
                emergency_keywords = match_result.get("emergency_keywords", [])
                logger.warning(f"🚨 실시간 응급 상황 감지! 키워드: {emergency_keywords}")
                
                # API 호출
                send_emergency_alert(text, emergency_keywords)
            
            # 채팅 히스토리에 추가
            add_to_vad_chat_history(timestamp, text, duration, is_emergency, emergency_keywords)
            
            # 누적된 히스토리 포맷팅하여 출력
            output = format_vad_chat_history()
            
            logger.info(f"🎤 VAD 인식 완료: {text}")
            yield output
        else:
            # 처리 중이거나 대기 중일 때
            # 기존 히스토리가 있으면 그대로 표시
            if len(vad_chat_history) > 0:
                output = format_vad_chat_history()
                
                # 처리 중 상태 추가
                if is_processing:
                    output += "\n\n🗣️ 음성 감지 중... 처리 중입니다."
                
                yield output
            else:
                # 히스토리가 없으면 대기 메시지
                if is_processing:
                    yield (
                        "🔴 음성인식 세션 활성화 중...\n\n"
                        "🗣️ 음성 감지 중... 처리 중입니다."
                    )
                else:
                    yield (
                        "🔴 음성인식 세션 활성화 중...\n\n"
                        "👂 대기 중... 말씀해주세요."
                    )

    except Exception as e:
        logger.error(f"❌ VAD 오디오 처리 오류: {e}", exc_info=True)
        yield f"❌ 오류: {str(e)}"


def collect_and_process_audio(audio_stream, language):
    """
    마이크 스트리밍 오디오 수집 및 실시간 처리 (레거시)
    """
    global stream_processor

    if audio_stream is None:
        yield ""
        return

    try:
        sr, audio_data = audio_stream

        if audio_data is None or len(audio_data) == 0:
            yield ""
            return

        logger.debug(f"오디오 수신: {len(audio_data)} samples, {sr}Hz")

        # 스테레오 → 모노 변환
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
            logger.debug("스테레오 → 모노 변환")

        # float32 정규화
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        elif audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # 16kHz 리샘플링
        if sr != 16000:
            audio_data = resample_audio(audio_data, sr, 16000)
            logger.debug(f"리샘플링: {sr}Hz → 16000Hz")

        # 프로세서 준비 확인
        if not stream_processor or not stream_processor.is_ready:
            logger.debug(f"프로세서 준비 안 됨: stream_processor={stream_processor is not None}, is_ready={stream_processor.is_ready if stream_processor else 'N/A'}")
            yield ""
            return

        # 오디오 청크 처리
        result_text = stream_processor.add_audio_chunk(audio_data)
        duration = stream_processor.get_current_duration()

        if result_text:
            match_result = matcher.find_best_match(result_text)
            logger.info(f"🎤 실시간 인식 ({duration:.1f}초): {match_result}")
            
            # 🚨 응급 상황 감지 시 API 호출
            if match_result.get("is_emergency", False):
                emergency_keywords = match_result.get("emergency_keywords", [])
                logger.warning(f"🚨 실시간 응급 상황 감지됨! 키워드: {emergency_keywords}")
                send_emergency_alert(result_text, emergency_keywords)
            
            yield f"🔴 녹음 중... ({duration:.1f}초)\n\n✅ 실시간 인식:\n{result_text}"
        else:
            last = stream_processor.last_result
            if last:
                yield f"🔴 녹음 중... ({duration:.1f}초)\n\n✅ 현재 인식:\n{last}"
            else:
                if stream_processor.is_recording:
                    yield f"🔴 녹음 중... ({duration:.1f}초)\n\n대기 중..."
                else:
                    yield ""

    except Exception as e:
        logger.error(f"❌ 오디오 처리 오류: {e}", exc_info=True)
        yield f"❌ 오류: {str(e)}"


# ====================
# 파일 업로드 음성인식
# ====================
def _resolve_file_path(audio_file):
    """파일 경로 추출"""
    if isinstance(audio_file, dict):
        return audio_file.get("path") or audio_file.get("name")
    if hasattr(audio_file, "name"):
        return audio_file.name
    return audio_file


def transcribe_file(audio_file, language):
    """파일 업로드 음성인식"""
    start_time = time.time()

    try:
        if audio_file is None:
            return "⚠️ 파일을 업로드해주세요."

        file_path = _resolve_file_path(audio_file)
        if not file_path or not os.path.exists(file_path):
            return f"❌ 파일 경로 오류: {file_path}"

        logger.info(f"⏱️ 파일 처리 시작: {file_path}")

        # 파일 읽기
        try:
            audio_data, sr = sf.read(file_path)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            samples = audio_data.astype(np.float32)
            sample_rate = sr
        except Exception as e1:
            logger.warning(f"soundfile 실패: {e1}, wave 시도")
            try:
                samples, sample_rate = read_wave(file_path)
            except Exception as e2:
                raise Exception(f"파일 읽기 실패. soundfile: {e1}, wave: {e2}")

        # 16kHz 리샘플링
        if sample_rate != 16000:
            logger.info(f"🔄 리샘플링: {sample_rate} Hz → 16000 Hz")
            samples = resample_audio(samples, sample_rate, 16000)
            sample_rate = 16000

        duration = len(samples) / sample_rate
        logger.info(f"🎤 음성인식 시작 - 길이: {duration:.2f}초")

        # Offline Recognizer로 처리
        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, samples)
        recognizer.decode_stream(stream)
        result = stream.result

        text = result.text.strip()

        # 정답 매칭
        match_result = matcher.find_best_match(text)

        if not text:
            text = "⚠️ 음성을 인식하지 못했습니다."

        file_name = os.path.basename(file_path)
        logger.info(f"📁 {file_name}\n{match_result}\n")

        total_time = time.time() - start_time
        logger.info(f"✅ 변환 완료: {text}")
        logger.info(f"⏱️ 처리 시간: {total_time:.2f}초")

        return text

    except Exception as e:
        logger.error(f"파일 처리 오류: {e}", exc_info=True)
        return f"❌ 오류: {str(e)}"


# ====================
# 🔹 배치 처리 (CSV 생성 기능 통합)
# ====================
# 배치 처리 결과 저장소
batch_results_storage = {
    "file_names": [],
    "ground_truths": [],
    "asr_results": []
}


def batch_transcribe(files, language):
    """배치 파일 처리"""
    global batch_results_storage

    if not files:
        return "⚠️ 파일을 업로드해주세요."

    # 결과 초기화
    batch_results_storage = {
        "file_names": [],
        "ground_truths": [],
        "asr_results": []
    }

    results = []
    total = len(files)

    for idx, file in enumerate(files, 1):
        try:
            file_path = _resolve_file_path(file)
            file_name = os.path.basename(file_path)
            logger.info(f"[{idx}/{total}] 처리 중: {file_name}")

            # 파일 읽기
            try:
                audio_data, sr = sf.read(file_path)
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                samples = audio_data.astype(np.float32)
                sample_rate = sr
            except Exception:
                try:
                    samples, sample_rate = read_wave(file_path)
                except Exception as e:
                    raise Exception(f"파일 읽기 실패: {e}")

            if sample_rate != 16000:
                samples = resample_audio(samples, sample_rate, 16000)
                sample_rate = 16000

            # Offline 처리
            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, samples)
            recognizer.decode_stream(stream)
            result = stream.result
            text = result.text.strip()

            # 정답 매칭
            match_result = matcher.find_best_match(text)
            best_match = match_result.get("best_match", "")

            if not text:
                text = "(음성 인식 실패)"

            # 결과 저장
            batch_results_storage["file_names"].append(file_name)
            batch_results_storage["ground_truths"].append(best_match)
            batch_results_storage["asr_results"].append(text)

            results.append(f"📁 **{file_name}**\n{text}\n")
            logger.info(f"📁 **{file_name}**\n{match_result}\n")

        except Exception as e:
            results.append(f"📁 **{file_name}**\n❌ 오류: {str(e)}\n")
            logger.error(f"파일 처리 실패: {file_name} - {e}")

            # 오류 발생 시에도 저장
            batch_results_storage["file_names"].append(file_name)
            batch_results_storage["ground_truths"].append("")
            batch_results_storage["asr_results"].append(f"ERROR: {str(e)}")

    output = f"✅ 총 {total}개 파일 처리 완료\n\n" + "\n".join(results)
    return output


def generate_batch_csv_handler():
    """배치 테스트 CSV 리포트 생성 핸들러"""
    if not batch_results_storage["file_names"]:
        return None, "⚠️ 생성할 배치 테스트 결과가 없습니다. 먼저 배치 변환을 진행해주세요."

    # CSV 생성
    csv_path = generate_batch_csv_report(
        file_names=batch_results_storage["file_names"],
        ground_truths=batch_results_storage["ground_truths"],
        asr_results=batch_results_storage["asr_results"],
        matcher=matcher
    )

    if csv_path and os.path.exists(csv_path):
        count = len(batch_results_storage["file_names"])
        return csv_path, f"✅ CSV 리포트 생성 완료!\n\n📊 총 {count}개 파일 처리\n📁 파일: {csv_path}"
    else:
        return None, "❌ CSV 리포트 생성 실패"


# ====================
# UI 생성
# ====================
def create_ui():
    """Gradio UI 생성"""

    css = """
    /* 출력 박스 스타일 - 채팅 스타일 */
    .output-box textarea {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.8;
        overflow-y: auto !important;
        max-height: 600px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    /* 스크롤바 스타일 */
    .output-box textarea::-webkit-scrollbar {
        width: 12px;
    }
    
    .output-box textarea::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .output-box textarea::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    
    .output-box textarea::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    """

    with gr.Blocks(
        title="안전관리 솔루션 음성감지 AI 테스트",
        css=css,
    ) as demo:
        gr.Markdown("""
        # 🎙️ 안전관리 솔루션 음성감지 AI 테스트

        RK3588 NPU 최적화 실시간 음성인식 시스템 (v4 - CSV 리포트 기능 추가)
        """)

        with gr.Tabs():
            # 탭 1: VAD 기반 실시간 음성인식
            with gr.Tab("🎤 실시간 음성인식 (VAD)"):
                gr.Markdown("""
                ### VAD 기반 실시간 음성인식 시스템 (v5 - VAD 자동 감지)

                🔧 **v5 신규 기능**:
                - ✅ **VAD (Voice Activity Detection)** - 음성 자동 감지
                - ✅ **간편한 사용** - 마이크 버튼만 클릭하면 자동 인식 시작
                - ✅ **자동 ASR-STT** - 음성 감지 시 자동으로 인식
                - ✅ **응급 상황 실시간 감지** - 키워드 기반 즉시 알림
                - ✅ 세션별 CSV 리포트 자동 생성
                """)

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        ### 🎤 마이크 입력
                        
                        **사용 방법:**
                        1. 아래 마이크 버튼(🎤) 클릭
                        2. 말하기 시작 - 자동으로 인식됩니다
                        3. 침묵하면 자동으로 다음 음성 대기
                        4. 종료하려면 "음성인식 종료" 버튼 클릭
                        """)
                        
                        audio_stream_vad = gr.Audio(
                            sources=["microphone"],
                            type="numpy",
                            streaming=True,
                            label="🎙️ 마이크 (클릭하여 시작)",
                        )

                        language_stream_vad = gr.Dropdown(
                            choices=["자동 감지", "한국어", "중국어", "영어", "일본어", "광동어"],
                            value="자동 감지",
                            label="🌐 언어 선택",
                        )

                        ground_truth_input_vad = gr.Textbox(
                            label="📝 정답 (Ground Truth) 입력 (선택사항)",
                            placeholder="예: 도와줘 사람이 쓰러졌어",
                            lines=2
                        )

                        with gr.Row():
                            stop_vad_btn = gr.Button("⏹️ 음성인식 종료", variant="stop", size="lg")
                            reset_vad_btn = gr.Button("🔄 새로 시작", variant="secondary", size="sm")

                    with gr.Column(scale=1):
                        output_stream_vad = gr.Textbox(
                            label="📄 실시간 음성인식 결과 (채팅 스타일)",
                            lines=20,
                            max_lines=30,
                            elem_classes="output-box",
                            autoscroll=True,
                            show_copy_button=True,
                        )

                gr.Markdown("### 📊 세션 관리 및 CSV 리포트")

                with gr.Row():
                    generate_csv_btn_vad = gr.Button("📥 CSV 리포트 생성", variant="secondary", size="lg")
                    clear_sessions_btn_vad = gr.Button("🗑️ 세션 초기화", variant="stop", size="sm")

                csv_output_file_vad = gr.File(label="📁 생성된 CSV 파일")
                csv_status_vad = gr.Textbox(label="📊 CSV 생성 상태", lines=3)

                gr.Markdown("""
                #### 💡 간편한 사용법
                1. 🎤 **마이크 버튼 클릭** → 녹음 시작 (브라우저가 마이크 권한 요청)
                2. 🗣️ **말하기** → VAD가 자동 감지하여 실시간 인식
                3. 🔇 **잠시 침묵** → 자동으로 구간 구분 및 결과 표시
                4. 🔄 **계속 말하기** → 여러 구간 연속 인식 가능
                5. ⏹️ **"음성인식 종료"** → 세션 종료 및 전체 결과 확인
                6. 📝 **(선택) 정답 입력** → CSV 리포트 생성 시 활용
                
                #### ⚡ v5 특징 (VAD 기반)
                - 🎯 **완전 자동** - 마이크만 클릭하면 자동으로 음성 감지 시작
                - ⏱️ **실시간 표시** - 음성 구간마다 즉시 결과 화면 표시
                - 🚨 **응급 즉시 알림** - 응급 키워드 감지 시 API 자동 호출
                - 📊 **구간별 저장** - 각 음성 구간 개별 저장 및 관리
                - 🔇 **자동 구간 분리** - 침묵 1.5초 감지로 자동 구간 구분
                
                #### ⚙️ 조정 가능한 설정
                - **에너지 임계값**: 0.01 (낮을수록 작은 소리도 감지)
                - **침묵 판단**: 1.5초 (침묵으로 인식하는 시간)
                - **최소 음성 길이**: 0.5초 (이보다 짧으면 무시)
                """)

                # 오디오 스트림 처리
                audio_stream_vad.stream(
                    fn=process_vad_audio_stream,
                    inputs=[audio_stream_vad, language_stream_vad],
                    outputs=output_stream_vad,
                )

                stop_vad_btn.click(
                    fn=stop_vad_session_handler,
                    inputs=[ground_truth_input_vad],
                    outputs=[output_stream_vad, ground_truth_input_vad],
                )
                
                reset_vad_btn.click(
                    fn=reset_vad_session_handler,
                    inputs=None,
                    outputs=[audio_stream_vad, output_stream_vad, ground_truth_input_vad],
                )

                generate_csv_btn_vad.click(
                    fn=generate_mic_csv_handler,
                    inputs=None,
                    outputs=[csv_output_file_vad, csv_status_vad]
                )

                clear_sessions_btn_vad.click(
                    fn=clear_mic_sessions_handler,
                    inputs=None,
                    outputs=csv_status_vad
                )

            # 탭 2: 기존 방식 (레거시)
            with gr.Tab("🎤 실시간 음성인식 (기존 방식)"):
                gr.Markdown("""
                ### 실시간 스트리밍 음성인식 (v4 - 기존 방식)

                🔧 **v4 기능**:
                - ✅ 마이크 세션 결과 자동 누적 저장
                - ✅ 세션별 CSV 리포트 자동 생성
                - ✅ 세션 결과 초기화 기능
                - ✅ 정답(Ground Truth) 입력 지원
                """)

                with gr.Row():
                    with gr.Column(scale=1):
                        audio_stream = gr.Audio(
                            sources=["microphone"],
                            type="numpy",
                            streaming=True,
                            label="🎙️ 마이크 (실시간 수집)",
                        )

                        language_stream = gr.Dropdown(
                            choices=["자동 감지", "한국어", "중국어", "영어", "일본어", "광동어"],
                            value="자동 감지",
                            label="🌐 언어 선택",
                        )

                        ground_truth_input = gr.Textbox(
                            label="📝 정답 (Ground Truth) 입력 (선택사항)",
                            placeholder="예: 회의는 오후 세 시에 시작해 알림 설정해 줘",
                            lines=2
                        )

                        with gr.Row():
                            start_btn = gr.Button("🎙️ 녹음 시작", variant="primary", size="lg")
                            stop_btn = gr.Button("⏹️ 녹음 종료", variant="stop", size="lg")

                    with gr.Column(scale=1):
                        output_stream = gr.Textbox(
                            label="📄 실시간 음성인식 결과",
                            lines=15,
                            elem_classes="output-box",
                            #show_copy_button=True,
                        )

                gr.Markdown("### 📊 세션 관리 및 CSV 리포트")

                with gr.Row():
                    generate_csv_btn = gr.Button("📥 CSV 리포트 생성", variant="secondary", size="lg")
                    clear_sessions_btn = gr.Button("🗑️ 세션 초기화", variant="stop", size="sm")

                csv_output_file = gr.File(label="📁 생성된 CSV 파일")
                csv_status = gr.Textbox(label="📊 CSV 생성 상태", lines=3)

                gr.Markdown("""
                #### 💡 사용 방법
                1. 🟡 **"녹음 시작" 버튼 클릭** → 준비 완료
                2. 📝 **(선택) 정답(Ground Truth) 입력** → CSV 리포트에 사용
                3. 🎤 **마이크 버튼 클릭** → 자동 녹음 시작
                4. 🗣️ **말하기** → 2초마다 실시간 인식
                5. ⏹️ **"녹음 종료" 버튼 클릭** → 결과 저장 및 최종 결과 표시
                6. 🔄 **반복 테스트 가능** → 여러 세션 누적 저장
                7. 📥 **"CSV 리포트 생성" 클릭** → 모든 세션 결과를 CSV 파일로 저장
                8. 🗑️ **"세션 초기화" 클릭** → 저장된 모든 세션 결과 삭제

                #### ⚡ v4 특징
                - ✅ 세션별 결과 자동 누적 (메모리 효율적)
                - ✅ CER(Character Error Rate) 자동 계산
                - ✅ CSV 파일 다운로드 지원
                - ✅ 정답 입력으로 정확한 평가 가능
                """)

                start_btn.click(
                    fn=start_recording_handler,
                    inputs=None,
                    outputs=[start_btn, stop_btn, audio_stream, output_stream],
                )

                stop_btn.click(
                    fn=stop_recording_handler,
                    inputs=[ground_truth_input],
                    outputs=[start_btn, stop_btn, output_stream, ground_truth_input],
                )

                audio_stream.stream(
                    fn=collect_and_process_audio,
                    inputs=[audio_stream, language_stream],
                    outputs=output_stream,
                )

                generate_csv_btn.click(
                    fn=generate_mic_csv_handler,
                    inputs=None,
                    outputs=[csv_output_file, csv_status]
                )

                clear_sessions_btn.click(
                    fn=clear_mic_sessions_handler,
                    inputs=None,
                    outputs=csv_status
                )

            # 탭 2: 파일 업로드
            with gr.Tab("📁 파일 업로드"):
                gr.Markdown("### 오디오 파일 업로드\nWAV, MP3, FLAC, M4A 등 지원")

                with gr.Row():
                    with gr.Column(scale=1):
                        audio_file = gr.File(
                            label="📁 오디오 파일 업로드",
                            file_types=["audio"],
                        )

                        language_file = gr.Dropdown(
                            choices=["자동 감지", "한국어", "중국어", "영어", "일본어", "광동어"],
                            value="자동 감지",
                            label="🌐 언어 선택",
                        )

                        transcribe_btn = gr.Button("🚀 변환 시작", variant="primary", size="lg")
                        clear_btn = gr.Button("🗑️ 초기화", size="sm")

                    with gr.Column(scale=1):
                        output_file = gr.Textbox(
                            label="📄 변환 결과",
                            lines=15,
                            elem_classes="output-box",
                            #show_copy_button=True,
                        )

                transcribe_btn.click(
                    fn=transcribe_file,
                    inputs=[audio_file, language_file],
                    outputs=output_file,
                )

                clear_btn.click(
                    fn=lambda: (None, ""),
                    outputs=[audio_file, output_file],
                )

            # 탭 3: 배치 처리 (CSV 생성 기능 통합)
            with gr.Tab("📦 배치 변환"):
                gr.Markdown("""
                ### 📥 여러 파일 일괄 처리 및 CSV 리포트 생성

                🔧 **v4 신규 기능**:
                - ✅ 배치 처리 결과 자동 저장
                - ✅ CSV 리포트 자동 생성 (CER 포함)
                """)

                with gr.Row():
                    with gr.Column():
                        batch_files = gr.File(
                            file_count="multiple",
                            label="오디오 파일들을 선택하세요",
                            file_types=["audio"],
                        )

                        batch_language = gr.Dropdown(
                            choices=["자동 감지", "한국어", "중국어", "영어", "일본어", "광동어"],
                            value="자동 감지",
                            label="🌐 언어 선택",
                        )

                        batch_btn = gr.Button("🚀 일괄 변환", variant="primary", size="lg")

                    with gr.Column():
                        batch_output = gr.Textbox(
                            label="📄 일괄 변환 결과",
                            lines=20,
                            #show_copy_button=True,
                        )

                gr.Markdown("### 📊 배치 테스트 CSV 리포트")

                generate_batch_csv_btn = gr.Button("📥 CSV 리포트 생성", variant="secondary", size="lg")

                batch_csv_output_file = gr.File(label="📁 생성된 CSV 파일")
                batch_csv_status = gr.Textbox(label="📊 CSV 생성 상태", lines=3)

                batch_btn.click(
                    fn=batch_transcribe,
                    inputs=[batch_files, batch_language],
                    outputs=batch_output,
                )

                generate_batch_csv_btn.click(
                    fn=generate_batch_csv_handler,
                    inputs=None,
                    outputs=[batch_csv_output_file, batch_csv_status]
                )

        gr.Markdown("""
        ---
        <div style="text-align: center; color: #666; padding: 20px;">
            Powered by Sherpa-ONNX + Gradio | RK3588 NPU | v4 (CSV 리포트 기능 추가)
        </div>
        """)

    return demo


# ====================
# 메인 실행
# ====================
if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Sherpa-ONNX Sense-Voice 음성인식 UI 시작")
    logger.info("🖥️ RK3588 NPU 최적화 (v4 - CSV 리포트 기능 추가)")
    logger.info("=" * 60 + "\n")

    try:
        load_model()
    except Exception as e:
        logger.error(f"\n❌ 모델 로딩 실패: {e}", exc_info=True)
        logger.error("\n프로그램 종료")
        exit(1)

    demo = create_ui()
    demo.queue()

    logger.info("\n" + "=" * 60)
    logger.info("🌐 웹 서버 시작...")
    logger.info("💡 RK3588 NPU 4코어 사용:")
    logger.info("   taskset 0x0F python asr_test_improved.py")
    logger.info("=" * 60)

    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            inbrowser=False,
            ssl_keyfile="server.key",
            ssl_certfile="server.crt",
        )
    except Exception as e:
        # SSL 검증 오류는 무시하고 서버는 계속 실행됨
        if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
            logger.warning(f"⚠️ SSL 검증 경고 (무시됨): {e}")
            logger.info("✅ 서버는 정상적으로 실행 중입니다. 브라우저에서 접속해주세요.")
            # 서버가 이미 시작되었으므로 무한 대기
            import time
            while True:
                time.sleep(1)
        else:
            raise
