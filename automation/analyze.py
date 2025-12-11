"""
단독 실행 POM 분석 스크립트
"""
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent))

from config import DriverFactory, TestConfig
from pom_analyzer import POMAnalyzer


def analyze_website(url: str, page_name: str) -> None:
    """
    웹사이트 분석 및 리포트 생성
    
    Args:
        url: 분석할 웹사이트 URL
        page_name: 페이지 이름
    """
    print(f"\n{'='*50}")
    print(f"POM 분석 시작: {page_name}")
    print(f"{'='*50}")
    
    driver = None
    try:
        # 드라이버 생성
        driver = DriverFactory.create_driver(TestConfig.BROWSER)
        
        # 페이지 열기
        print(f"페이지 열기: {url}")
        driver.get(url)
        
        # 분석
        analyzer = POMAnalyzer(driver)
        results = analyzer.analyze_page_elements(page_name)
        
        # 결과 출력
        print("\n[분석 결과]")
        print(f"  URL: {results['url']}")
        print(f"  제목: {results['title']}")
        print(f"  요소 수: {len(results['elements'])}")
        print(f"  입력 필드: {len(results['inputs'])}")
        print(f"  버튼: {len(results['buttons'])}")
        print(f"  링크: {len(results['links'])}")
        print(f"  이미지: {len(results['images'])}")
        
        # 상호작용 요소 찾기
        print("\n[상호작용 요소]")
        interactive = analyzer.find_interactive_elements()
        print(f"  버튼: {len(interactive['buttons'])}")
        print(f"  링크: {len(interactive['links'])}")
        print(f"  입력 필드: {len(interactive['inputs'])}")
        print(f"  체크박스: {len(interactive['checkboxes'])}")
        print(f"  라디오 버튼: {len(interactive['radio_buttons'])}")
        print(f"  셀렉트: {len(interactive['selects'])}")
        
        # 입력 필드 상세정보
        if results['inputs']:
            print("\n[입력 필드 상세]")
            for inp in results['inputs'][:5]:
                print(f"  - ID: {inp.get('id')}, Type: {inp.get('type')}, Placeholder: {inp.get('placeholder')}")
        
        # 버튼 상세정보
        if results['buttons']:
            print("\n[버튼 상세]")
            for btn in results['buttons'][:5]:
                print(f"  - ID: {btn.get('id')}, Text: {btn.get('text')}")
        
        # JSON 내보내기
        output_dir = Path(__file__).parent / "reports"
        output_dir.mkdir(exist_ok=True)
        
        json_file = output_dir / f"{page_name}_analysis.json"
        analyzer.export_analysis_to_json(str(json_file))
        print(f"\n✓ JSON 리포트 저장: {json_file}")
        
        # POM 코드 생성
        class_name = ''.join(word.capitalize() for word in page_name.split('_')) + "Page"
        pom_code = analyzer.generate_pom_code(page_name, class_name)
        
        pom_file = output_dir / f"{page_name}_pom.py"
        pom_file.write_text(pom_code, encoding='utf-8')
        print(f"✓ POM 코드 생성: {pom_file}")
        
        # 요약
        print("\n" + analyzer.get_summary())
        
    finally:
        if driver:
            DriverFactory.close_driver(driver)
        print(f"\n{'='*50}\n")


def main():
    """메인 함수"""
    # 분석할 페이지 목록
    pages_to_analyze = [
        ("http://localhost:3000/login", "login"),
        ("http://localhost:3000/dashboard", "dashboard"),
        ("http://localhost:3000/settings", "settings"),
    ]
    
    print("\n" + "="*50)
    print("🔍 웹 POM 자동 분석 도구")
    print("="*50)
    
    for url, page_name in pages_to_analyze:
        try:
            analyze_website(url, page_name)
        except Exception as e:
            print(f"❌ 분석 실패 ({page_name}): {str(e)}")
            continue


if __name__ == "__main__":
    main()
