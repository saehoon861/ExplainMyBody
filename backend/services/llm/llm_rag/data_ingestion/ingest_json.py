"""
JSON 형식 RAG 데이터를 PostgreSQL paper_nodes 테이블에 입력
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()


class RAGDataIngestion:
    """RAG 데이터 입력 클래스"""

    def __init__(self, db_url: Optional[str] = None):
        """
        Args:
            db_url: PostgreSQL 연결 URL (없으면 환경변수에서 가져옴)
        """
        if not db_url:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")

        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """JSON 파일 로드"""
        print(f"\n📂 JSON 파일 로딩: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"  ✓ 파일 로드 완료")
        print(f"  노드 수: {len(data.get('nodes', []))}")
        print(f"  엣지 수: {len(data.get('links', []))}")

        return data

    def parse_paper_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """JSON 데이터에서 Paper 노드만 추출 및 파싱"""
        paper_nodes = []

        for node in data.get('nodes', []):
            if node.get('node_type') == 'paper':
                paper = {
                    'paper_id': node.get('id', '').replace('paper_', ''),
                    'title': node.get('title', ''),
                    'chunk_text': node.get('chunk_text', ''),
                    'chunk_ko_summary': node.get('chunk_ko_summary', ''),
                    'lang': node.get('lang', 'en'),
                    'source': node.get('source', 'unknown'),
                    'year': node.get('year'),
                    'pmid': node.get('pmid'),
                    'doi': node.get('doi'),
                    'embedding_ko': node.get('embedding_ko'),
                    'embedding_en': node.get('embedding_en')
                }
                paper_nodes.append(paper)

        print(f"\n  📄 Paper 노드 파싱 완료: {len(paper_nodes)}개")
        return paper_nodes

    def insert_papers_to_db(
        self,
        papers: List[Dict[str, Any]],
        batch_size: int = 100,
        skip_existing: bool = True
    ):
        """
        Paper 데이터를 PostgreSQL에 삽입

        Args:
            papers: Paper 노드 리스트
            batch_size: 배치 삽입 크기
            skip_existing: 이미 존재하는 paper_id는 스킵
        """
        session = self.SessionLocal()

        try:
            print(f"\n💾 PostgreSQL에 데이터 삽입 중... (배치 크기: {batch_size})")

            inserted_count = 0
            skipped_count = 0
            error_count = 0

            for i in range(0, len(papers), batch_size):
                batch = papers[i:i+batch_size]

                for paper in batch:
                    try:
                        # 중복 확인
                        if skip_existing:
                            existing = session.execute(
                                text("SELECT id FROM paper_nodes WHERE paper_id = :paper_id"),
                                {"paper_id": paper['paper_id']}
                            ).fetchone()

                            if existing:
                                skipped_count += 1
                                continue

                        # Embedding을 PostgreSQL array 형식으로 변환
                        embedding_ko_str = None
                        if paper.get('embedding_ko'):
                            embedding_ko_str = "[" + ",".join(str(x) for x in paper['embedding_ko']) + "]"

                        embedding_en_str = None
                        if paper.get('embedding_en'):
                            embedding_en_str = "[" + ",".join(str(x) for x in paper['embedding_en']) + "]"

                        # INSERT 쿼리
                        insert_query = text("""
                            INSERT INTO paper_nodes (
                                paper_id, title, chunk_text, chunk_ko_summary,
                                lang, source, year, pmid, doi,
                                embedding_ko_openai, embedding_en_openai,
                                created_at, updated_at
                            )
                            VALUES (
                                :paper_id, :title, :chunk_text, :chunk_ko_summary,
                                :lang, :source, :year, :pmid, :doi,
                                :embedding_ko, :embedding_en,
                                NOW(), NOW()
                            )
                        """)

                        session.execute(insert_query, {
                            'paper_id': paper['paper_id'],
                            'title': paper['title'],
                            'chunk_text': paper['chunk_text'],
                            'chunk_ko_summary': paper['chunk_ko_summary'],
                            'lang': paper['lang'],
                            'source': paper['source'],
                            'year': paper['year'],
                            'pmid': paper['pmid'],
                            'doi': paper['doi'],
                            'embedding_ko': embedding_ko_str,
                            'embedding_en': embedding_en_str
                        })

                        inserted_count += 1

                    except Exception as e:
                        error_count += 1
                        print(f"  ⚠️  에러 (paper_id: {paper.get('paper_id')}): {e}")
                        continue

                # 배치 커밋
                session.commit()
                print(f"  진행: {min(i+batch_size, len(papers))}/{len(papers)} papers...")

            print(f"\n✅ 삽입 완료!")
            print(f"  - 삽입: {inserted_count}개")
            print(f"  - 스킵: {skipped_count}개")
            print(f"  - 에러: {error_count}개")

        except Exception as e:
            session.rollback()
            print(f"\n❌ 데이터 삽입 실패: {e}")
            raise
        finally:
            session.close()

    def run(self, json_file_path: str, batch_size: int = 100, skip_existing: bool = True):
        """전체 프로세스 실행"""
        print("=" * 60)
        print("RAG 데이터 입력 (JSON → PostgreSQL)")
        print("=" * 60)

        # 1. JSON 파일 로드
        data = self.load_json_file(json_file_path)

        # 2. Paper 노드 파싱
        papers = self.parse_paper_nodes(data)

        if not papers:
            print("\n⚠️  Paper 노드가 없습니다.")
            return

        # 3. DB 삽입
        self.insert_papers_to_db(papers, batch_size=batch_size, skip_existing=skip_existing)

        print("\n" + "=" * 60)
        print("✅ 완료!")
        print("=" * 60)


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="RAG 데이터 입력 (JSON → PostgreSQL)")
    parser.add_argument(
        "json_file",
        type=str,
        help="입력할 JSON 파일 경로"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="배치 삽입 크기 (기본: 100)"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="이미 존재하는 데이터도 다시 삽입 (기본: 스킵)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="PostgreSQL 연결 URL (기본: 환경변수 DATABASE_URL)"
    )

    args = parser.parse_args()

    # 실행
    ingestion = RAGDataIngestion(db_url=args.db_url)
    ingestion.run(
        json_file_path=args.json_file,
        batch_size=args.batch_size,
        skip_existing=not args.no_skip_existing
    )


if __name__ == "__main__":
    main()
