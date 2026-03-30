"""
export.py - 쿼리 결과를 CSV로 내보내는 유틸리티 (Phase 2 구현 예정)
"""

import csv
import io
from typing import Any
from pathlib import Path


def export_to_csv(
    data: list[dict[str, Any]],
    filepath: str | Path | None = None,
) -> str:
    """
    딕셔너리 리스트를 CSV 문자열로 반환하거나 파일로 저장합니다.

    Args:
        data: execute_query()의 반환값 (딕셔너리 리스트)
        filepath: 저장할 파일 경로. None이면 문자열만 반환.

    Returns:
        CSV 형식 문자열
    """
    if not data:
        return "결과 데이터가 없습니다."

    headers = list(data[0].keys())

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)

    csv_string = output.getvalue()

    if filepath:
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            f.write(csv_string)

    return csv_string
