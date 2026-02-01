"""
Graph RAG 데이터 Import Script
- graph_rag_*.json 파일을 PostgreSQL (pgvector) 및 Neo4j에 로드
- PaperNode 테이블에 논문 데이터 삽입
- PaperConceptRelation 테이블에 관계 데이터 삽입
- 선택적으로 Neo4j에 그래프 구조 생성

Usage:
    python backend/utils/scripts/import_graph_rag.py [--json-path PATH] [--neo4j] [--clear]

Options:
    --json-path: graph_rag JSON 파일 경로 (기본: 최신 파일 자동 탐색)
    --neo4j: Neo4j에도 데이터 로드 (기본: False)
    --clear: 기존 데이터 삭제 후 재로드 (기본: False)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# 프로젝트 루트 경로 추가 (backend/ 디렉토리)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from database import engine, SessionLocal
from models.paper_node import PaperNode
from models.paper_concept_relation import PaperConceptRelation
from repositories.neo4j_repository import Neo4jRepository


def find_latest_graph_rag_json(base_path: str = "src/llm/ragdb_collect/outputs") -> Optional[str]:
    """최신 graph_rag JSON 파일 찾기"""
    # backend/utils/scripts/ → backend/utils/ → backend/ → project_root
    project_root = Path(__file__).parent.parent.parent.parent
    outputs_dir = project_root / base_path

    if not outputs_dir.exists():
        print(f"❌ 출력 디렉토리를 찾을 수 없습니다: {outputs_dir}")
        return None

    # graph_rag_*papers_*.json 패턴 파일 찾기 (stats 파일 제외)
    json_files = list(outputs_dir.glob("graph_rag_*papers_*.json"))

    # stats 파일 제외
    json_files = [f for f in json_files if 'stats' not in f.name]

    if not json_files:
        print(f"❌ graph_rag JSON 파일을 찾을 수 없습니다: {outputs_dir}")
        return None

    # 최신 파일 선택 (수정 시간 기준)
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ 최신 JSON 파일 발견: {latest_file}")
    return str(latest_file)


def load_graph_rag_json(file_path: str) -> Dict[str, Any]:
    """graph_rag JSON 파일 로드"""
    print(f"\n📂 JSON 파일 로드 중: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    num_nodes = len(data.get('nodes', []))
    num_edges = len(data.get('edges', []))

    print(f"  ✓ Nodes: {num_nodes:,}개")
    print(f"  ✓ Edges: {num_edges:,}개")

    return data


def enable_pgvector_extension():
    """pgvector extension 활성화"""
    print("\n🔧 pgvector extension 확인 중...")

    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("  ✓ pgvector extension 활성화 완료")
    except Exception as e:
        print(f"  ⚠️  pgvector extension 활성화 실패: {e}")
        print("     수동으로 설치하세요: sudo apt-get install postgresql-<version>-pgvector")


def create_tables():
    """테이블 생성"""
    print("\n🔧 테이블 생성 중...")

    from database import Base

    try:
        Base.metadata.create_all(bind=engine, tables=[
            PaperNode.__table__,
            PaperConceptRelation.__table__
        ])
        print("  ✓ 테이블 생성 완료 (paper_nodes, paper_concept_relations)")
    except Exception as e:
        print(f"  ⚠️  테이블 생성 실패: {e}")


def clear_existing_data(session):
    """기존 데이터 삭제"""
    print("\n🗑️  기존 데이터 삭제 중...")

    try:
        # CASCADE 삭제로 관계 데이터도 자동 삭제됨
        deleted_relations = session.query(PaperConceptRelation).delete()
        deleted_papers = session.query(PaperNode).delete()
        session.commit()

        print(f"  ✓ 삭제 완료: {deleted_papers:,}개 논문, {deleted_relations:,}개 관계")
    except Exception as e:
        session.rollback()
        print(f"  ❌ 삭제 실패: {e}")
        raise


def import_papers_to_postgres(nodes: List[Dict[str, Any]], session) -> Dict[str, int]:
    """논문 데이터를 PostgreSQL에 bulk insert"""
    # Paper 노드만 필터링 (Concept 노드 제외)
    paper_nodes = [n for n in nodes if n.get('node_type') == 'paper']
    concept_nodes = [n for n in nodes if n.get('node_type') != 'paper']

    print(f"\n📥 PostgreSQL에 {len(paper_nodes):,}개 논문 삽입 중... (총 {len(nodes):,}개 노드 중 {len(concept_nodes):,}개 개념 노드 제외)")

    paper_id_map = {}  # paper_id -> db_id 매핑
    batch_size = 500
    total_inserted = 0
    total_skipped = 0

    for i in range(0, len(paper_nodes), batch_size):
        batch = paper_nodes[i:i + batch_size]
        paper_objects = []

        for node in batch:
            try:
                # embedding_ko를 embedding_ko_openai로 매핑
                embedding_ko_openai = node.get('embedding_ko')

                # PaperNode 객체 생성
                paper = PaperNode(
                    paper_id=node['id'],
                    title=node['title'],
                    chunk_text=node['chunk_text'],
                    lang=node['lang'],
                    chunk_ko_summary=node.get('chunk_ko_summary'),
                    domain=node.get('domain'),
                    source=node.get('source', 'unknown'),
                    year=node.get('year'),
                    pmid=node.get('pmid'),
                    doi=node.get('doi'),
                    authors=None,  # JSON 파일에 없음
                    journal=None,  # JSON 파일에 없음
                    keywords=None,  # JSON 파일에 없음
                    embedding_ko_openai=embedding_ko_openai,
                    embedding_openai=None,  # 나중에 생성
                    embedding_ollama=None,  # 나중에 생성
                    embedding_provider=node.get('embedding_provider', 'openai'),
                )

                paper_objects.append(paper)

            except Exception as e:
                print(f"    ⚠️  Paper {node.get('id')} 파싱 실패: {e}")
                total_skipped += 1
                continue

        # Bulk insert
        if paper_objects:
            try:
                session.bulk_save_objects(paper_objects, return_defaults=True)
                session.commit()

                # ID 매핑 생성 (나중에 관계 삽입 시 사용)
                for paper in paper_objects:
                    # re-query to get DB ID
                    db_paper = session.query(PaperNode).filter(
                        PaperNode.paper_id == paper.paper_id
                    ).first()
                    if db_paper:
                        paper_id_map[paper.paper_id] = db_paper.id

                total_inserted += len(paper_objects)
                # 5 배치마다 또는 완료 시 진행률 출력 (출력 최소화)
                batch_num = i // batch_size
                if batch_num % 5 == 0 or total_inserted >= len(paper_nodes):
                    print(f"  ✓ 진행: {total_inserted:,}/{len(paper_nodes):,} ({100*total_inserted/len(paper_nodes):.1f}%)")

            except IntegrityError as e:
                session.rollback()
                print(f"    ⚠️  배치 삽입 실패 (중복 가능성): {e}")
                total_skipped += len(paper_objects)
            except Exception as e:
                session.rollback()
                print(f"    ❌ 배치 삽입 실패: {e}")
                total_skipped += len(paper_objects)

    print(f"\n  ✅ 논문 삽입 완료: {total_inserted:,}개 성공, {total_skipped:,}개 스킵")
    return paper_id_map


def import_relations_to_postgres(
    edges: List[Dict[str, Any]],
    paper_id_map: Dict[str, int],
    session
):
    """관계 데이터를 PostgreSQL에 bulk insert"""
    print(f"\n📥 PostgreSQL에 {len(edges):,}개 관계 삽입 중...")

    batch_size = 1000
    total_inserted = 0
    total_skipped = 0
    missing_papers = set()  # 누락된 paper_id 추적

    for i in range(0, len(edges), batch_size):
        batch = edges[i:i + batch_size]
        relation_objects = []

        for edge in batch:
            source_paper_id = edge['source']
            target_concept_id = edge['target']

            # paper_id를 DB ID로 변환
            db_paper_id = paper_id_map.get(source_paper_id)

            if not db_paper_id:
                total_skipped += 1
                missing_papers.add(source_paper_id)
                continue

            try:
                relation = PaperConceptRelation(
                    paper_id=db_paper_id,
                    concept_id=target_concept_id,
                    relation_type=edge.get('type', 'MENTIONS'),
                    confidence=edge.get('confidence') or 0.5,
                    matched_term=edge.get('matched_term'),
                    count=edge.get('count', 1),
                    evidence_level=None,  # 추후 추가 가능
                    magnitude=None,  # 추후 추가 가능
                    concept_name_ko=None,  # 추후 추가 가능
                    concept_name_en=None,  # 추후 추가 가능
                    concept_type=None,  # 추후 추가 가능
                )

                relation_objects.append(relation)

            except Exception as e:
                print(f"    ⚠️  Relation {edge} 파싱 실패: {e}")
                total_skipped += 1
                continue

        # Bulk insert
        if relation_objects:
            try:
                session.bulk_save_objects(relation_objects)
                session.commit()

                total_inserted += len(relation_objects)
                # 10 배치마다 또는 완료 시 진행률 출력 (출력 최소화)
                batch_num = i // batch_size
                if batch_num % 10 == 0 or total_inserted >= len(edges):
                    print(f"  ✓ 진행: {total_inserted:,}/{len(edges):,} ({100*total_inserted/len(edges):.1f}%)")

            except Exception as e:
                session.rollback()
                print(f"    ❌ 배치 삽입 실패: {e}")
                total_skipped += len(relation_objects)

    print(f"\n  ✅ 관계 삽입 완료: {total_inserted:,}개 성공, {total_skipped:,}개 스킵")

    if missing_papers:
        print(f"  ℹ️  스킵 이유: {len(missing_papers):,}개 논문이 DB에 없음 (논문 삽입 실패 또는 JSON에 누락)")
        if len(missing_papers) <= 10:
            print(f"     누락된 paper_id: {', '.join(list(missing_papers)[:10])}")
        else:
            print(f"     누락된 paper_id 샘플 (처음 10개): {', '.join(list(missing_papers)[:10])}")


def import_to_neo4j(data: Dict[str, Any]):
    """Neo4j에 그래프 데이터 로드 (선택적)"""
    print("\n🔷 Neo4j에 그래프 데이터 로드 중...")

    try:
        neo4j_repo = Neo4jRepository()

        if not neo4j_repo.driver:
            print("  ⚠️  Neo4j 연결 실패. 스킵합니다.")
            return

        nodes = data.get('nodes', [])
        edges = data.get('edges', [])

        # Paper와 Concept 노드 분리
        paper_nodes = [n for n in nodes if n.get('node_type') == 'paper']
        concept_nodes = [n for n in nodes if n.get('node_type') != 'paper']

        print(f"  - {len(paper_nodes):,}개 Paper 노드 생성 중...")

        # Paper 노드 생성
        batch_size = 500
        with neo4j_repo.driver.session() as session:
            for i in range(0, len(paper_nodes), batch_size):
                batch = paper_nodes[i:i + batch_size]

                for node in batch:
                    session.run("""
                        MERGE (p:Paper {id: $id})
                        SET p.title = $title,
                            p.lang = $lang,
                            p.domain = $domain,
                            p.source = $source,
                            p.year = $year,
                            p.pmid = $pmid,
                            p.doi = $doi
                    """,
                        id=node['id'],
                        title=node['title'],
                        lang=node['lang'],
                        domain=node.get('domain'),
                        source=node.get('source'),
                        year=node.get('year'),
                        pmid=node.get('pmid'),
                        doi=node.get('doi')
                    )

                if (i // batch_size) % 3 == 0 or i + batch_size >= len(paper_nodes):
                    print(f"    ✓ Paper 노드: {min(i+batch_size, len(paper_nodes)):,}/{len(paper_nodes):,}")

        # Concept 노드 생성
        print(f"  - {len(concept_nodes):,}개 Concept 노드 생성 중...")
        with neo4j_repo.driver.session() as session:
            for node in concept_nodes:
                session.run("""
                    MERGE (c:Concept {id: $id})
                    SET c.name = $id
                """,
                    id=node['id']
                )

            print(f"    ✓ Concept 노드: {len(concept_nodes):,}개 생성 완료")

        print(f"  - {len(edges):,}개 관계 생성 중...")

        # 관계 생성 (배치)
        with neo4j_repo.driver.session() as session:
            for i in range(0, len(edges), batch_size):
                batch = edges[i:i + batch_size]

                for edge in batch:
                    # 관계 생성 (동적 타입)
                    relation_type = edge.get('type', 'MENTIONS')
                    source_id = edge['source']
                    target_id = edge['target']

                    # source가 Paper인지 Concept인지 구분 (paper_ 접두사로 판단)
                    if source_id.startswith('paper_'):
                        # Paper → Concept 관계
                        session.run(f"""
                            MATCH (p:Paper {{id: $source_id}})
                            MATCH (c:Concept {{id: $target_id}})
                            MERGE (p)-[r:{relation_type}]->(c)
                            SET r.confidence = $confidence,
                                r.matched_term = $matched_term,
                                r.count = $count
                        """,
                            source_id=source_id,
                            target_id=target_id,
                            confidence=edge.get('confidence') or 0.5,
                            matched_term=edge.get('matched_term'),
                            count=edge.get('count', 1)
                        )
                    else:
                        # Concept → Concept 관계
                        session.run(f"""
                            MATCH (c1:Concept {{id: $source_id}})
                            MATCH (c2:Concept {{id: $target_id}})
                            MERGE (c1)-[r:{relation_type}]->(c2)
                            SET r.confidence = $confidence,
                                r.matched_term = $matched_term,
                                r.count = $count
                        """,
                            source_id=source_id,
                            target_id=target_id,
                            confidence=edge.get('confidence') or 0.5,
                            matched_term=edge.get('matched_term'),
                            count=edge.get('count', 1)
                        )

                # 10 배치마다 진행률 출력
                if (i // batch_size) % 10 == 0 or i + batch_size >= len(edges):
                    print(f"    ✓ 관계: {min(i+batch_size, len(edges)):,}/{len(edges):,}")

        print("  ✅ Neo4j 로드 완료")
        neo4j_repo.close()

    except Exception as e:
        print(f"  ❌ Neo4j 로드 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Graph RAG 데이터를 PostgreSQL 및 Neo4j에 로드")
    parser.add_argument(
        "--json-path",
        type=str,
        help="graph_rag JSON 파일 경로 (기본: 최신 파일 자동 탐색)"
    )
    parser.add_argument(
        "--neo4j",
        action="store_true",
        help="Neo4j에도 데이터 로드"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="기존 데이터 삭제 후 재로드"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("  Graph RAG Data Import Script")
    print("="*60)

    # 1. JSON 파일 찾기
    json_path = args.json_path or find_latest_graph_rag_json()

    if not json_path:
        print("\n❌ JSON 파일을 찾을 수 없습니다.")
        print("   --json-path 옵션으로 직접 지정하세요.")
        return

    # 2. JSON 로드
    data = load_graph_rag_json(json_path)

    # 3. pgvector extension 활성화
    enable_pgvector_extension()

    # 4. 테이블 생성
    create_tables()

    # 5. PostgreSQL 데이터 삽입
    session = SessionLocal()

    try:
        # 기존 데이터 삭제 (선택적)
        if args.clear:
            clear_existing_data(session)

        # 논문 삽입
        paper_id_map = import_papers_to_postgres(data['nodes'], session)

        # 관계 삽입
        import_relations_to_postgres(data['edges'], paper_id_map, session)

    except Exception as e:
        print(f"\n❌ PostgreSQL 삽입 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

    # 6. Neo4j 로드 (선택적)
    if args.neo4j:
        import_to_neo4j(data)

    print("\n" + "="*60)
    print("  ✅ Graph RAG 데이터 Import 완료!")
    print("="*60)
    print(f"\n📊 요약:")
    print(f"  - 총 논문: {len(data['nodes']):,}개")
    print(f"  - 총 관계: {len(data['edges']):,}개")
    print(f"  - PostgreSQL: paper_nodes, paper_concept_relations 테이블")
    if args.neo4j:
        print(f"  - Neo4j: Paper, Concept 노드 및 관계 그래프")
    print()


if __name__ == "__main__":
    main()
