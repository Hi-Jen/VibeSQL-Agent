import pandas as pd
from typing import List, Dict, Any
import os

class DataExporter:
    """
    쿼리 결과를 CSV 또는 Excel 파일로 변환하는 유틸리티.
    """
    @staticmethod
    def to_csv(data: List[Dict[str, Any]], filename: str = "query_result.csv") -> str:
        """
        데이터 리스트를 CSV로 저장함 (utf-8-sig 인코딩으로 한글 깨짐 방지).
        """
        if not data:
            return ""
        
        df = pd.DataFrame(data)
        os.makedirs("exports", exist_ok=True)
        path = os.path.join("exports", filename)
        df.to_csv(path, index=False, encoding='utf-8-sig')
        return path

    @staticmethod
    def to_excel(data: List[Dict[str, Any]], filename: str = "query_result.xlsx") -> str:
        """
        데이터 리스트를 Excel로 저장함.
        """
        if not data:
            return ""
            
        df = pd.DataFrame(data)
        os.makedirs("exports", exist_ok=True)
        path = os.path.join("exports", filename)
        df.to_excel(path, index=False)
        return path
