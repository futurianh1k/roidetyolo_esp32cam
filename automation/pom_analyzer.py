"""
POM 분석 및 검증 유틸리티
"""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from typing import List, Dict, Tuple
import json
from datetime import datetime


class POMAnalyzer:
    """POM 구조 분석 및 검증"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.analysis_results = {}
    
    def analyze_page_elements(self, page_name: str) -> Dict:
        """
        페이지의 모든 요소 분석
        
        Args:
            page_name: 페이지 이름
        
        Returns:
            분석 결과 딕셔너리
        """
        results = {
            "page_name": page_name,
            "timestamp": datetime.now().isoformat(),
            "url": self.driver.current_url,
            "title": self.driver.title,
            "elements": self._get_all_elements(),
            "inputs": self._get_all_inputs(),
            "buttons": self._get_all_buttons(),
            "links": self._get_all_links(),
            "images": self._get_all_images(),
        }
        
        self.analysis_results[page_name] = results
        return results
    
    def _get_all_elements(self) -> List[Dict]:
        """모든 요소 수집"""
        elements = []
        
        for element in self.driver.find_elements(By.CSS_SELECTOR, "*"):
            try:
                tag_name = element.tag_name
                element_id = element.get_attribute("id")
                class_name = element.get_attribute("class")
                
                if tag_name and (element_id or class_name):
                    elements.append({
                        "tag": tag_name,
                        "id": element_id,
                        "class": class_name,
                        "text": element.text[:50] if element.text else "",
                    })
            except:
                continue
        
        return elements
    
    def _get_all_inputs(self) -> List[Dict]:
        """모든 입력 요소 수집"""
        inputs = []
        
        for element in self.driver.find_elements(By.TAG_NAME, "input"):
            try:
                inputs.append({
                    "id": element.get_attribute("id"),
                    "name": element.get_attribute("name"),
                    "type": element.get_attribute("type"),
                    "placeholder": element.get_attribute("placeholder"),
                })
            except:
                continue
        
        return inputs
    
    def _get_all_buttons(self) -> List[Dict]:
        """모든 버튼 수집"""
        buttons = []
        
        for element in self.driver.find_elements(By.TAG_NAME, "button"):
            try:
                buttons.append({
                    "id": element.get_attribute("id"),
                    "class": element.get_attribute("class"),
                    "text": element.text,
                    "type": element.get_attribute("type"),
                })
            except:
                continue
        
        return buttons
    
    def _get_all_links(self) -> List[Dict]:
        """모든 링크 수집"""
        links = []
        
        for element in self.driver.find_elements(By.TAG_NAME, "a"):
            try:
                links.append({
                    "href": element.get_attribute("href"),
                    "text": element.text,
                    "id": element.get_attribute("id"),
                })
            except:
                continue
        
        return links
    
    def _get_all_images(self) -> List[Dict]:
        """모든 이미지 수집"""
        images = []
        
        for element in self.driver.find_elements(By.TAG_NAME, "img"):
            try:
                images.append({
                    "src": element.get_attribute("src"),
                    "alt": element.get_attribute("alt"),
                    "id": element.get_attribute("id"),
                })
            except:
                continue
        
        return images
    
    def find_interactive_elements(self) -> Dict[str, List]:
        """상호작용 가능한 요소 찾기"""
        interactive = {
            "buttons": [],
            "links": [],
            "inputs": [],
            "selects": [],
            "checkboxes": [],
            "radio_buttons": [],
        }
        
        # 버튼
        for btn in self.driver.find_elements(By.TAG_NAME, "button"):
            try:
                interactive["buttons"].append({
                    "text": btn.text,
                    "id": btn.get_attribute("id"),
                    "visible": btn.is_displayed(),
                })
            except:
                continue
        
        # 링크
        for link in self.driver.find_elements(By.TAG_NAME, "a"):
            try:
                interactive["links"].append({
                    "text": link.text,
                    "href": link.get_attribute("href"),
                    "visible": link.is_displayed(),
                })
            except:
                continue
        
        # 입력 필드
        for inp in self.driver.find_elements(By.TAG_NAME, "input"):
            try:
                inp_type = inp.get_attribute("type")
                if inp_type == "checkbox":
                    interactive["checkboxes"].append({
                        "id": inp.get_attribute("id"),
                        "name": inp.get_attribute("name"),
                    })
                elif inp_type == "radio":
                    interactive["radio_buttons"].append({
                        "id": inp.get_attribute("id"),
                        "name": inp.get_attribute("name"),
                    })
                else:
                    interactive["inputs"].append({
                        "id": inp.get_attribute("id"),
                        "type": inp_type,
                        "placeholder": inp.get_attribute("placeholder"),
                    })
            except:
                continue
        
        # 셀렉트
        for select in self.driver.find_elements(By.TAG_NAME, "select"):
            try:
                interactive["selects"].append({
                    "id": select.get_attribute("id"),
                    "name": select.get_attribute("name"),
                })
            except:
                continue
        
        return interactive
    
    def export_analysis_to_json(self, filepath: str) -> None:
        """분석 결과를 JSON 파일로 내보내기"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
    
    def generate_pom_code(self, page_name: str, class_name: str) -> str:
        """
        분석 결과를 기반으로 POM 코드 생성
        
        Args:
            page_name: 페이지 이름
            class_name: 클래스 이름
        
        Returns:
            생성된 Python POM 코드
        """
        results = self.analysis_results.get(page_name)
        if not results:
            return ""
        
        code = f'''"""
{page_name} Page Object Model
자동 생성된 POM 코드
"""
from selenium.webdriver.common.by import By
from base_page import BasePage


class {class_name}(BasePage):
    """{page_name} 페이지 객체"""
    
    # Locators
'''
        
        # 입력 필드 로케이터 추가
        for inp in results.get("inputs", [])[:10]:
            if inp.get("id"):
                locator_name = inp["id"].upper().replace("-", "_")
                code += f'    {locator_name} = (By.ID, "{inp["id"]}")\n'
        
        # 버튼 로케이터 추가
        for btn in results.get("buttons", [])[:10]:
            if btn.get("id"):
                locator_name = btn["id"].upper().replace("-", "_")
                code += f'    {locator_name} = (By.ID, "{btn["id"]}")\n'
        
        code += '''
    def __init__(self, driver):
        super().__init__(driver)
    
    # 페이지 메서드들을 여기에 추가하세요
'''
        
        return code
    
    def get_summary(self) -> str:
        """분석 요약 정보"""
        summary = "=== POM 분석 요약 ===\n"
        
        for page_name, results in self.analysis_results.items():
            summary += f"\n페이지: {page_name}\n"
            summary += f"  URL: {results.get('url')}\n"
            summary += f"  제목: {results.get('title')}\n"
            summary += f"  요소 수: {len(results.get('elements', []))}\n"
            summary += f"  입력 필드: {len(results.get('inputs', []))}\n"
            summary += f"  버튼: {len(results.get('buttons', []))}\n"
            summary += f"  링크: {len(results.get('links', []))}\n"
            summary += f"  이미지: {len(results.get('images', []))}\n"
        
        return summary
