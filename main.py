"""
main.py - VibeSQL-Agent CLI 진입점

터미널에서 자연어 질문을 입력받아 SQL로 변환하고 실행합니다.
"""

import sys
import logging
from tabulate import tabulate

from src.core.engine import VibeQLEngine

# 로깅 설정: Self-Correction 과정을 터미널에서 확인할 수 있도록
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def print_banner() -> None:
    """시작 배너를 출력합니다."""
    banner = """
╔══════════════════════════════════════════════════╗
║              ⚡ VibeSQL-Agent v0.1              ║
║    자연어로 안전하게 SQL을 실행하는 AI 에이전트     ║
╠══════════════════════════════════════════════════╣
║  💬 자연어 질문을 입력하세요 (예: 개발팀 직원 목록) ║
║  🚫 위험한 쿼리(DELETE, DROP 등)는 자동 차단됩니다.║
║  🔄 SQL 에러 시 최대 3회 자동 수정을 시도합니다.   ║
║  📤 'quit' 또는 'exit'로 종료합니다.              ║
╚══════════════════════════════════════════════════╝
"""
    print(banner)


def print_result(response: dict) -> None:
    """에이전트 실행 결과를 보기 좋게 출력합니다."""
    print(f"\n{'─' * 50}")
    print(f"📝 질문: {response['question']}")
    print(f"{'─' * 50}")

    if response["retries"] > 0:
        print(f"🔄 Self-Correction: {response['retries']}회 재시도")

    print(f"\n🔍 생성된 SQL:")
    print(f"   {response['sql']}")

    if response["success"]:
        result = response["result"]
        if result:
            print(f"\n✅ 결과 ({len(result)}건):")
            # tabulate로 깔끔한 테이블 출력
            print(tabulate(result, headers="keys", tablefmt="rounded_grid"))
        else:
            print("\n✅ 쿼리가 성공했지만 결과가 없습니다.")
    else:
        print(f"\n❌ 실행 실패: {response['error']}")

    print()


def main() -> None:
    """CLI 메인 루프."""
    print_banner()

    # 엔진 초기화 (인메모리 데모 DB 자동 생성)
    try:
        engine = VibeQLEngine()
        print("✅ 엔진 초기화 완료 (데모 DB 로드됨)\n")
    except Exception as e:
        print(f"❌ 엔진 초기화 실패: {e}")
        sys.exit(1)

    # 스키마 정보 출력 (필요 시 전체 스키마를 db_manager를 통해 직접 조회 가능)
    print("📊 Dynamic Schema 모드 활성화됨")
    print("   (질문에 따라 필요한 테이블만 선별적으로 참조합니다.)\n")

    # 대화형 루프
    while True:
        try:
            question = input("💬 질문 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 VibeSQL-Agent를 종료합니다.")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print("👋 VibeSQL-Agent를 종료합니다.")
            break

        # 자연어 → SQL 변환 및 실행
        response = engine.generate_and_execute(question)
        print_result(response)


if __name__ == "__main__":
    main()
