"""
기존 논문에 한국어 요약 추가 생성
- DB의 paper_nodes 테이블에서 chunk_text가 있지만 chunk_ko_summary가 없는 논문 찾기
- exaone3.5:7.8b로 한국어 요약 생성
- DB 업데이트
"""

import psycopg2
import os
from dotenv import load_dotenv
import time
from typing import Optional

try:
    import ollama
    USE_OLLAMA = True
except ImportError:
    USE_OLLAMA = False
    print("❌ Ollama 없음. pip install ollama 실행")
    exit(1)

load_dotenv()


def generate_korean_summary(english_abstract: str, model: str = "exaone3.5:7.8b") -> Optional[str]:
    """
    영어 초록을 한국어로 요약

    Args:
        english_abstract: 영어 초록
        model: Ollama 모델

    Returns:
        한국어 요약 (실패 시 None)
    """
    try:
        prompt = f"""다음 영어 논문 초록을 읽고 핵심 내용을 2-3문장의 한국어로 요약하세요.
다음 정보를 반드시 포함하세요:
1. 주요 연구 목적
2. 핵심 결과 (숫자/수치 포함)
3. 임상적 의의

체성분, 근육, 영양, 운동 관련 키워드를 정확히 번역하세요.

논문 초록:
{english_abstract}

한국어 요약:"""

        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.6,
                "num_predict": 300
            }
        )

        summary = response['message']['content'].strip()
        return summary

    except Exception as e:
        print(f"  ⚠️ 요약 실패: {e}")
        return None


def main():
    """메인 실행 함수"""

    print("=" * 70)
    print("🇰🇷 한국어 요약 생성 (exaone3.5:7.8b)")
    print("=" * 70)
    print()

    # DB 연결
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL 환경변수가 없습니다.")
        return

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # 한국어 요약이 없는 논문 찾기
    cursor.execute("""
        SELECT id, paper_id, title, chunk_text
        FROM paper_nodes
        WHERE (chunk_text IS NOT NULL AND chunk_text != '' AND LENGTH(chunk_text) >= 50)
          AND (chunk_ko_summary IS NULL OR chunk_ko_summary = '')
        ORDER BY id
    """)

    papers = cursor.fetchall()
    total = len(papers)

    print(f"📊 한국어 요약 생성 대상: {total}개 논문")
    print()

    if total == 0:
        print("✅ 모든 논문에 한국어 요약이 있습니다!")
        cursor.close()
        conn.close()
        return

    # 사용자 확인
    print(f"⚠️  {total}개 논문에 대해 한국어 요약을 생성합니다.")
    print(f"⚠️  예상 소요 시간: 약 {total * 1.5 / 60:.1f}분")
    print()
    user_input = input("계속 진행하시겠습니까? (y/n): ")
    if user_input.lower() != 'y':
        print("❌ 취소되었습니다.")
        cursor.close()
        conn.close()
        return

    print()
    print("=" * 70)
    print("🚀 한국어 요약 생성 시작")
    print("=" * 70)
    print()

    success_count = 0
    fail_count = 0

    for i, (paper_id, paper_pid, title, chunk_text) in enumerate(papers, 1):
        print(f"[{i}/{total}] {paper_pid}")
        print(f"  Title: {title[:60]}...")

        # 한국어 요약 생성
        ko_summary = generate_korean_summary(chunk_text)

        if ko_summary:
            # DB 업데이트
            try:
                cursor.execute("""
                    UPDATE paper_nodes
                    SET chunk_ko_summary = %s
                    WHERE id = %s
                """, (ko_summary, paper_id))
                conn.commit()

                print(f"  ✅ 요약: {ko_summary[:80]}...")
                success_count += 1

            except Exception as e:
                print(f"  ❌ DB 업데이트 실패: {e}")
                conn.rollback()
                fail_count += 1

        else:
            fail_count += 1

        # Progress
        if i % 10 == 0:
            print(f"\n  📊 진행률: {i}/{total} ({i/total*100:.1f}%) | 성공: {success_count} | 실패: {fail_count}\n")

        # Rate limiting
        time.sleep(0.3)

    print()
    print("=" * 70)
    print("✅ 한국어 요약 생성 완료")
    print("=" * 70)
    print(f"  성공: {success_count}개")
    print(f"  실패: {fail_count}개")
    print(f"  총: {total}개")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
