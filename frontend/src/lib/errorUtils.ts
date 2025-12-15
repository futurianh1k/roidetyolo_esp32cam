/**
 * API 오류 메시지 추출 유틸리티
 * 
 * Pydantic validation error, 일반 에러 등 다양한 형태의 오류 응답을
 * 사용자에게 표시할 수 있는 문자열로 변환합니다.
 */

export function getErrorMessage(error: any, defaultMessage: string = '오류가 발생했습니다'): string {
  // Axios 에러인 경우
  const detail = error?.response?.data?.detail;
  
  if (!detail) {
    // 에러 메시지가 없으면 기본 메시지
    return error?.message || defaultMessage;
  }
  
  // 문자열인 경우 그대로 반환
  if (typeof detail === 'string') {
    return detail;
  }
  
  // 배열인 경우 (Pydantic validation errors)
  if (Array.isArray(detail)) {
    return detail
      .map((e: any) => {
        if (typeof e === 'string') return e;
        return e.msg || e.message || JSON.stringify(e);
      })
      .join(', ');
  }
  
  // 객체인 경우
  if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  
  return defaultMessage;
}
