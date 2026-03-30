"""
dictionary.py - YAML 도메인 용어 사전 파싱 모듈

config/dictionary.yaml을 읽어 LLM 프롬프트에 주입할
도메인 용어 매핑 컨텍스트를 문자열로 반환합니다.
"""

import os
from pathlib import Path
from typing import Any

import yaml


# 프로젝트 루트 기준 사전 파일 경로
_DEFAULT_DICT_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "dictionary.yaml"
)


def load_dictionary(path: str | Path | None = None) -> dict[str, Any]:
    """
    YAML 사전 파일을 파싱하여 딕셔너리로 반환합니다.

    Args:
        path: 사전 파일 경로. None이면 기본 경로 사용.

    Returns:
        파싱된 도메인 사전 딕셔너리

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
    """
    dict_path = Path(path) if path else _DEFAULT_DICT_PATH

    if not dict_path.exists():
        raise FileNotFoundError(
            f"도메인 사전 파일을 찾을 수 없습니다: {dict_path}"
        )

    with open(dict_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data or {}


def get_dictionary_context(path: str | Path | None = None) -> str:
    """
    도메인 사전을 LLM 프롬프트에 주입할 수 있는 문자열로 변환합니다.

    Returns:
        도메인 용어 매핑을 설명하는 텍스트 블록
        예:
          [인사팀 도메인 용어]
          - "직원" → employees 테이블
          - "급여" → salary 컬럼
    """
    data = load_dictionary(path)
    domains = data.get("domains", {})

    if not domains:
        return "도메인 사전이 비어있습니다."

    parts: list[str] = []

    for domain_name, domain_info in domains.items():
        synonyms = domain_info.get("synonyms", {})
        if not synonyms:
            continue

        lines = [f"[{domain_name} 도메인 용어]"]
        for korean_term, sql_mapping in synonyms.items():
            lines.append(f'  - "{korean_term}" → {sql_mapping}')

        parts.append("\n".join(lines))

    return "\n\n".join(parts)
