"""
Cypher 형식 RAG 데이터를 PostgreSQL에 입력
Neo4j Cypher 파일을 파싱하여 PostgreSQL paper_nodes 및 paper_concept_relations 테이블에 저장
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()


class CypherDataIngestion:
    """Cypher 데이터 입력 클래스"""

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

    def load_cypher_file(self, file_path: str) -> str:
        """Cypher 파일 로드"""
        print(f"\n📂 Cypher 파일 로딩: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            cypher_content = f.read()

        print(f"  ✓ 파일 로드 완료 ({len(cypher_content)} 문자)")
        return cypher_content

    def parse_concepts(self, cypher_content: str) -> List[Dict[str, Any]]:
        """Cypher에서 Concept 노드 파싱"""
        # CREATE (cCONCEPT_ID:Concept:TYPE {id: '...', name_ko: '...', ...});
        pattern = r"CREATE \(c(\w+):Concept(?::(\w+))?\s*\{([^}]+)\}\);"

        concepts = []
        for match in re.finditer(pattern, cypher_content):
            concept_var = match.group(1)
            concept_type = match.group(2) or 'Unknown'
            properties_str = match.group(3)

            # 속성 파싱
            props = {}
            for prop_match in re.finditer(r"(\w+):\s*'([^']+)'|(\w+):\s*([\d.]+)", properties_str):
                if prop_match.group(1):  # 문자열 속성
                    props[prop_match.group(1)] = prop_match.group(2)
                else:  # 숫자 속성
                    props[prop_match.group(3)] = float(prop_match.group(4))

            concepts.append({
                'concept_id': props.get('id', concept_var),
                'name_ko': props.get('name_ko', ''),
                'name_en': props.get('name_en', ''),
                'concept_type': concept_type,
                'importance': props.get('importance', 0.5)
            })

        print(f"\n  🔷 Concept 노드 파싱: {len(concepts)}개")
        return concepts

    def parse_papers(self, cypher_content: str) -> List[Dict[str, Any]]:
        """Cypher에서 Paper 노드 파싱"""
        # CREATE (pPAPER_ID:Paper {id: 'paper_...', title: '...'});
        pattern = r"CREATE \(p(paper_\d+):Paper\s*\{([^}]+)\}\);"

        papers = []
        for match in re.finditer(pattern, cypher_content):
            paper_var = match.group(1)
            properties_str = match.group(2)

            # 속성 파싱
            props = {}
            for prop_match in re.finditer(r"(\w+):\s*'([^']*)'", properties_str):
                props[prop_match.group(1)] = prop_match.group(2)

            papers.append({
                'paper_id': props.get('id', paper_var).replace('paper_', ''),
                'title': props.get('title', '')
            })

        print(f"  📄 Paper 노드 파싱: {len(papers)}개")
        return papers

    def parse_relations(self, cypher_content: str) -> List[Dict[str, Any]]:
        """Cypher에서 Paper-Concept 관계 파싱"""
        # CREATE (pPAPER)-[:RELATION {confidence: 0.8}]->(cCONCEPT);
        pattern = r"CREATE \((p\w+)\)-\[:(\w+)\s*(?:\{([^}]+)\})?\]->\((c\w+)\);"

        relations = []
        for match in re.finditer(pattern, cypher_content):
            paper_var = match.group(1)
            relation_type = match.group(2)
            properties_str = match.group(3) or ''
            concept_var = match.group(4)

            # 속성 파싱
            confidence = 0.5
            evidence_level = 'medium'

            if properties_str:
                conf_match = re.search(r"confidence:\s*([\d.]+)", properties_str)
                if conf_match:
                    confidence = float(conf_match.group(1))

                level_match = re.search(r"evidence_level:\s*'(\w+)'", properties_str)
                if level_match:
                    evidence_level = level_match.group(1)

            relations.append({
                'paper_var': paper_var,
                'concept_var': concept_var,
                'relation_type': relation_type,
                'confidence': confidence,
                'evidence_level': evidence_level
            })

        print(f"  🔗 관계 파싱: {len(relations)}개")
        return relations

    def insert_concepts_to_db(self, concepts: List[Dict[str, Any]], skip_existing: bool = True):
        """Concept 데이터를 PostgreSQL에 삽입 (개념 테이블이 있다면)"""
        # 개념 테이블이 없을 수도 있으므로 optional
        print(f"\n💾 Concept 데이터 삽입 스킵 (개념 테이블 미사용)")
        # 필요시 구현

    def insert_papers_to_db(self, papers: List[Dict[str, Any]], skip_existing: bool = True):
        """Paper 데이터를 PostgreSQL에 삽입 (제목만)"""
        session = self.SessionLocal()

        try:
            print(f"\n💾 Paper 데이터 삽입 중...")

            inserted_count = 0
            skipped_count = 0

            for paper in papers:
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

                    # INSERT (제목만, 나머지는 NULL)
                    insert_query = text("""
                        INSERT INTO paper_nodes (
                            paper_id, title, created_at, updated_at
                        )
                        VALUES (
                            :paper_id, :title, NOW(), NOW()
                        )
                    """)

                    session.execute(insert_query, {
                        'paper_id': paper['paper_id'],
                        'title': paper['title']
                    })

                    inserted_count += 1

                except Exception as e:
                    print(f"  ⚠️  에러 (paper_id: {paper.get('paper_id')}): {e}")
                    continue

            session.commit()

            print(f"  ✓ Paper 삽입 완료: {inserted_count}개 (스킵: {skipped_count}개)")

        except Exception as e:
            session.rollback()
            print(f"\n❌ Paper 삽입 실패: {e}")
            raise
        finally:
            session.close()

    def run(self, cypher_file_path: str, skip_existing: bool = True):
        """전체 프로세스 실행"""
        print("=" * 60)
        print("RAG 데이터 입력 (Cypher → PostgreSQL)")
        print("=" * 60)

        # 1. Cypher 파일 로드
        cypher_content = self.load_cypher_file(cypher_file_path)

        # 2. 파싱
        concepts = self.parse_concepts(cypher_content)
        papers = self.parse_papers(cypher_content)
        relations = self.parse_relations(cypher_content)

        # 3. DB 삽입
        if concepts:
            self.insert_concepts_to_db(concepts, skip_existing=skip_existing)

        if papers:
            self.insert_papers_to_db(papers, skip_existing=skip_existing)

        print(f"\n⚠️  관계 데이터는 paper_concept_relations 테이블에 별도 삽입 필요")
        print(f"  (총 {len(relations)}개 관계)")

        print("\n" + "=" * 60)
        print("✅ 완료!")
        print("=" * 60)


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="RAG 데이터 입력 (Cypher → PostgreSQL)")
    parser.add_argument(
        "cypher_file",
        type=str,
        help="입력할 Cypher 파일 경로"
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
    ingestion = CypherDataIngestion(db_url=args.db_url)
    ingestion.run(
        cypher_file_path=args.cypher_file,
        skip_existing=not args.no_skip_existing
    )


if __name__ == "__main__":
    main()
