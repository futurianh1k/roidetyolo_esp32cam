"""
테스트 결과를 마크다운 문서로 변환하는 스크립트
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


def load_test_results(json_path: Path) -> Dict:
    """JSON 테스트 결과 파일 로드"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_markdown_table(results: List[Dict]) -> str:
    """테스트 결과를 마크다운 테이블로 변환"""
    table = []
    table.append(
        "| 테스트 타입 | API 이름 | 메서드 | 엔드포인트 | 상태 코드 | 예상 상태 | 성공 여부 | 응답 시간 (ms) | 비고 |"
    )
    table.append(
        "|-----------|---------|--------|-----------|-----------|----------|----------|---------------|------|"
    )

    for result in results:
        test_type = result.get("test_type", "positive")
        test_type_label = "✅ Positive" if test_type == "positive" else "❌ Negative"
        api_name = result.get("api_name", "N/A")
        method = result.get("method", "N/A")
        endpoint = result.get("endpoint", "N/A")
        status_code = result.get("status_code", 0)
        expected_status = result.get("expected_status", "N/A")
        success = "✅ 성공" if result.get("success") else "❌ 실패"
        response_time = (
            f"{result.get('response_time_ms', 0):.2f}"
            if result.get("response_time_ms")
            else "N/A"
        )
        notes = result.get("notes", "") or result.get("error", "")

        # 상태 코드 색상 표시
        if status_code == 0:
            status_display = "연결 실패"
        elif 200 <= status_code < 300:
            status_display = f"✅ {status_code}"
        elif 400 <= status_code < 500:
            status_display = f"⚠️ {status_code}"
        else:
            status_display = f"❌ {status_code}"

        table.append(
            f"| {test_type_label} | {api_name} | {method} | `{endpoint}` | {status_display} | {expected_status} | {success} | {response_time} | {notes[:50]} |"
        )

    return "\n".join(table)


def generate_markdown_report(test_results_path: Path, output_path: Path):
    """마크다운 테스트 보고서 생성"""
    # 테스트 결과 로드
    data = load_test_results(test_results_path)

    summary = data.get("test_summary", {})
    results = data.get("test_results", [])

    # 마크다운 문서 생성
    md_content = []

    # 헤더
    md_content.append("# API 테스트 결과 보고서")
    md_content.append("")
    md_content.append(f"**테스트 실행 시간**: {summary.get('test_time', 'N/A')}")
    md_content.append("")

    # 요약
    md_content.append("## 테스트 요약")
    md_content.append("")
    md_content.append(f"- **총 테스트 수**: {summary.get('total', 0)}")
    md_content.append(f"- **성공**: {summary.get('success', 0)}")
    md_content.append(f"- **실패**: {summary.get('failed', 0)}")
    md_content.append(
        f"- **성공률**: {(summary.get('success', 0) / summary.get('total', 1) * 100):.1f}%"
    )
    md_content.append("")

    # Positive/Negative 테스트 분류
    positive_summary = summary.get("positive_tests", {})
    negative_summary = summary.get("negative_tests", {})

    if positive_summary or negative_summary:
        md_content.append("### 테스트 타입별 통계")
        md_content.append("")
        md_content.append("| 테스트 타입 | 총 테스트 | 성공 | 실패 | 성공률 |")
        md_content.append("|-----------|----------|------|------|--------|")

        if positive_summary:
            pos_total = positive_summary.get("total", 0)
            pos_success = positive_summary.get("success", 0)
            pos_failed = positive_summary.get("failed", 0)
            pos_rate = (pos_success / pos_total * 100) if pos_total > 0 else 0
            md_content.append(
                f"| ✅ Positive | {pos_total} | {pos_success} | {pos_failed} | {pos_rate:.1f}% |"
            )

        if negative_summary:
            neg_total = negative_summary.get("total", 0)
            neg_success = negative_summary.get("success", 0)
            neg_failed = negative_summary.get("failed", 0)
            neg_rate = (neg_success / neg_total * 100) if neg_total > 0 else 0
            md_content.append(
                f"| ❌ Negative | {neg_total} | {neg_success} | {neg_failed} | {neg_rate:.1f}% |"
            )

        md_content.append("")
        md_content.append("**참고**:")
        md_content.append("- **Positive 테스트**: 정상 동작을 검증하는 테스트")
        md_content.append(
            "- **Negative 테스트**: 예외 처리 및 에러 핸들링을 검증하는 테스트"
        )
        md_content.append("")

    # API 그룹별 통계
    md_content.append("## API 그룹별 통계")
    md_content.append("")

    api_groups = {}
    for result in results:
        endpoint = result.get("endpoint", "")
        if endpoint.startswith("/auth"):
            group = "인증 API"
        elif endpoint.startswith("/devices"):
            group = "장비 관리 API"
        elif endpoint.startswith("/control"):
            group = "장비 제어 API"
        elif endpoint.startswith("/audio"):
            group = "오디오 파일 관리 API"
        elif endpoint.startswith("/asr"):
            group = "ASR (음성인식) API"
        elif endpoint.startswith("/users"):
            group = "사용자 관리 API"
        elif endpoint in ["/", "/health"]:
            group = "시스템 API"
        else:
            group = "기타"

        if group not in api_groups:
            api_groups[group] = {"total": 0, "success": 0}

        api_groups[group]["total"] += 1
        if result.get("success"):
            api_groups[group]["success"] += 1

    md_content.append("| API 그룹 | 총 테스트 | 성공 | 실패 | 성공률 |")
    md_content.append("|---------|----------|------|------|--------|")
    for group, stats in sorted(api_groups.items()):
        total = stats["total"]
        success = stats["success"]
        failed = total - success
        rate = (success / total * 100) if total > 0 else 0
        md_content.append(f"| {group} | {total} | {success} | {failed} | {rate:.1f}% |")
    md_content.append("")

    # 상세 테스트 결과
    md_content.append("## 상세 테스트 결과")
    md_content.append("")
    md_content.append(generate_markdown_table(results))
    md_content.append("")

    # Negative 테스트 예외 처리 검증 결과
    negative_tests = [r for r in results if r.get("test_type") == "negative"]
    if negative_tests:
        md_content.append("## Negative 테스트 예외 처리 검증 결과")
        md_content.append("")
        md_content.append(
            "| API 이름 | 예상 상태 코드 | 실제 상태 코드 | 검증 결과 | 비고 |"
        )
        md_content.append("|---------|-------------|-------------|----------|------|")

        for result in negative_tests:
            expected = result.get("expected_status", "N/A")
            actual = result.get("status_code", "N/A")
            is_valid = result.get("success") and (
                actual == expected
                or (
                    isinstance(expected, int)
                    and isinstance(actual, int)
                    and actual in [400, 404, 422]
                )
            )
            validation_result = "✅ 통과" if is_valid else "❌ 실패"
            notes = result.get("notes", "") or result.get("error", "")

            md_content.append(
                f"| {result.get('api_name')} | {expected} | {actual} | {validation_result} | {notes[:50]} |"
            )

        md_content.append("")

    # 실패한 테스트 상세
    failed_tests = [r for r in results if not r.get("success")]
    if failed_tests:
        md_content.append("## 실패한 테스트 상세")
        md_content.append("")
        for result in failed_tests:
            test_type = result.get("test_type", "positive")
            test_type_label = "[POSITIVE]" if test_type == "positive" else "[NEGATIVE]"
            md_content.append(f"### {test_type_label} {result.get('api_name')}")
            md_content.append("")
            md_content.append(
                f"- **엔드포인트**: `{result.get('method')} {result.get('endpoint')}`"
            )
            md_content.append(f"- **상태 코드**: {result.get('status_code', 'N/A')}")
            if result.get("expected_status"):
                md_content.append(
                    f"- **예상 상태 코드**: {result.get('expected_status')}"
                )
            md_content.append(f"- **오류**: {result.get('error', 'N/A')}")
            md_content.append(f"- **비고**: {result.get('notes', 'N/A')}")
            md_content.append("")

    # 파일 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"✅ 마크다운 보고서가 생성되었습니다: {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python generate_test_report.py <test_results.json> [output.md]")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = json_path.parent / f"{json_path.stem}.md"

    generate_markdown_report(json_path, output_path)
