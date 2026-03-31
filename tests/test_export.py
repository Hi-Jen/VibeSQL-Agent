import os
from pathlib import Path
from src.utils.export import export_to_csv

def test_export_to_csv_results():
    """CSV 변환 및 파일 생성 로직을 검증합니다."""
    # 더미 데이터
    test_data = [
        {"name": "김철수", "department": "개발팀", "salary": 5000},
        {"name": "이영희", "department": "기획팀", "salary": 6000}
    ]
    
    test_file = Path("output/test_export.csv")
    if test_file.exists():
        os.remove(test_file)
        
    # 실행
    csv_string = export_to_csv(test_data, test_file)
    
    # 검증: 문자열 반환 확인
    assert "김철수,개발팀,5000" in csv_string
    assert "이영희,기획팀,6000" in csv_string
    
    # 검증: 파일 생성 확인
    assert test_file.exists()
    
    # 검증: 한글 인코딩 (BOM 확인)
    with open(test_file, "rb") as f:
        bom = f.read(3)
        assert bom == b'\xef\xbb\xbf' # UTF-8 SIG BOM

    # 정리
    os.remove(test_file)
