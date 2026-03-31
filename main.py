"""
main.py - VibeSQL-Agent CLI 진입점

터미널에서 자연어 질문을 입력받아 SQL로 변환하고 실행합니다.
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

from src.core.engine import VibeQLEngine
from src.utils.export import export_to_csv

# 로깅 설정
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
║  💬 자연어 질문을 입력하세요                             ║
║  📂 조회 결과는 CSV로 익스포트 가능합니다.              ║
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
            print(tabulate(result, headers="keys", tablefmt="rounded_grid"))
        else:
            print("\n✅ 쿼리가 성공했지만 결과가 없습니다.")
    else:
        print(f"\n❌ 실행 실패: {response['error']}")


def handle_export(data: list) -> None:
    """사용자 요청 시 데이터를 CSV로 저장합니다."""
    if not data:
        return

    choice = input("\n📊 결과를 CSV 파일로 저장하시겠습니까? (y/n): ").strip().lower()
    if choice == 'y':
        # output 디렉토리 보장
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # 타임스탬프 기반 파일명 생성
        filename = f"records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = output_dir / filename

        try:
            export_to_csv(data, filepath)
            print(f"💾 저장이 완료되었습니다: [ {filepath} ]")
        except Exception as e:
            print(f"❌ 저장 중 오류 발생: {e}")


def main() -> None:
    """CLI 메인 루프."""
    print_banner()

    try:
        engine = VibeQLEngine()
        print("✅ 엔진 초기화 완료 (데모 DB 로드됨)\n")
    except Exception as e:
        print(f"❌ 엔진 초기화 실패: {e}")
        sys.exit(1)

    print("📊 Dynamic Schema 모드 활성화됨")
    print("   (질문에 따라 필요한 테이블만 선별적으로 참조합니다.)\n")

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

        # 결과 저장 인터페이스 호출
        if response["success"] and response["result"]:
            handle_export(response["result"])


if __name__ == "__main__":
    main()
