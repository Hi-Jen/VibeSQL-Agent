from abc import ABC, abstractmethod
import yaml
from typing import Dict, Any, List

class BaseDictionary(ABC):
    """
    용어 사전 인터페이스. 나중에 DB 연동 등으로 확장 가능하도록 추상 클래스로 정의.
    """
    @abstractmethod
    def get_terms(self, department: str) -> Dict[str, Any]:
        """
        특정 부서의 용어 정의를 리턴함.
        """
        pass

    @abstractmethod
    def get_context_string(self, department: str) -> str:
        """
        LLM 프롬프트에 주입할 용어 정보 문자열을 리턴함.
        """
        pass

class YamlDictionary(BaseDictionary):
    """
    YAML 파일을 기반으로 하는 용어 사전 구현체.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading YAML dictionary: {e}")
            return {}

    def get_terms(self, department: str) -> Dict[str, Any]:
        return self.data.get("departments", {}).get(department, {}).get("terms", {})

    def get_context_string(self, department: str) -> str:
        terms = self.get_terms(department)
        if not terms:
            return "용어 사전에 정의된 내용이 없습니다."
        
        lines = []
        for term, info in terms.items():
            desc = info.get("description", "")
            clause = info.get("sql_condition", info.get("sql_calculation", ""))
            lines.append(f"- {term}: {desc} (Query Fragment: {clause})")
        
        return "\n".join(lines)
