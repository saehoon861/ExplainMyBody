"""
Neo4j Repository - Graph 탐색 (개념 ↔ 논문 관계)
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import os


class Neo4jRepository:
    """Neo4j Graph 탐색 Repository"""

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Args:
            uri: Neo4j URI (기본: localhost:7687)
            user: 사용자명 (기본: neo4j)
            password: 비밀번호 (환경변수에서 로드)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 연결 테스트
            self.driver.verify_connectivity()
            print(f"✅ Neo4j 연결 성공: {self.uri}")
        except Exception as e:
            print(f"⚠️ Neo4j 연결 실패: {e}")
            self.driver = None

    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()

    def get_papers_by_concept_graph(
        self,
        concept_id: str,
        relation_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        개념과 연결된 논문 조회 (Graph 탐색)

        Args:
            concept_id: muscle_hypertrophy 등
            relation_types: ['MENTIONS', 'INCREASES'] 등
            limit: 결과 개수

        Returns:
            논문 리스트
        """
        if not self.driver:
            return []

        # Cypher 쿼리
        if relation_types:
            rel_filter = f":{('|'.join(relation_types))}"
        else:
            rel_filter = ""

        # Paper → Concept 직접 연결 + Concept → Concept → Paper 간접 연결 모두 검색
        query = f"""
        MATCH (p:Paper)-[r{rel_filter}]->(c:Concept {{id: $concept_id}})
        RETURN p.id as paper_id, p.title as title, type(r) as relation_type, r.confidence as confidence
        UNION
        MATCH (p:Paper)-[r1{rel_filter}]->(c1:Concept)-[r2]->(c:Concept {{id: $concept_id}})
        WHERE c1 <> c
        RETURN p.id as paper_id, p.title as title, type(r1) as relation_type,
               (r1.confidence * 0.7 + r2.confidence * 0.3) as confidence
        ORDER BY confidence DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, concept_id=concept_id, limit=limit)
            papers = []
            for record in result:
                papers.append({
                    "paper_id": record["paper_id"],
                    "title": record["title"],
                    "relation_type": record["relation_type"],
                    "confidence": record["confidence"],
                })
            return papers

    def get_related_concepts(
        self, concept_id: str, relation_types: Optional[List[str]] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        개념과 관련된 다른 개념 조회 (공통 논문 기반)

        Args:
            concept_id: protein_intake 등
            relation_types: 관계 타입 필터
            limit: 결과 개수

        Returns:
            관련 개념 리스트
        """
        if not self.driver:
            return []

        # Cypher 쿼리 (개념 → 논문 → 다른 개념)
        if relation_types:
            rel_filter = f"[:{('|'.join(relation_types))}]"
        else:
            rel_filter = ""

        query = f"""
        MATCH (c1:Concept {{id: $concept_id}})<-{rel_filter}-(p:Paper)-{rel_filter}->(c2:Concept)
        WHERE c1 <> c2
        RETURN c2.id as concept_id, c2.name_ko as name_ko, c2.name_en as name_en,
               count(p) as共同_paper_count
        ORDER BY 共同_paper_count DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, concept_id=concept_id, limit=limit)
            concepts = []
            for record in result:
                concepts.append({
                    "concept_id": record["concept_id"],
                    "name_ko": record["name_ko"],
                    "name_en": record["name_en"],
                    "共同_paper_count": record["共同_paper_count"],
                })
            return concepts

    def expand_concepts(
        self, initial_concepts: List[str], max_depth: int = 2, limit_per_concept: int = 5
    ) -> List[str]:
        """
        개념 확장 (관련 개념 탐색)

        Args:
            initial_concepts: 초기 개념 리스트
            max_depth: 탐색 깊이
            limit_per_concept: 개념당 확장 개수

        Returns:
            확장된 개념 ID 리스트
        """
        if not self.driver:
            return initial_concepts

        expanded = set(initial_concepts)

        for concept in initial_concepts:
            related = self.get_related_concepts(concept, limit=limit_per_concept)
            for rel in related:
                expanded.add(rel["concept_id"])

            if len(expanded) > 50:  # 최대 50개로 제한
                break

        return list(expanded)

    def get_concept_info(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        개념 정보 조회

        Args:
            concept_id: muscle_hypertrophy 등

        Returns:
            개념 정보 또는 None
        """
        if not self.driver:
            return None

        query = """
        MATCH (c:Concept {id: $concept_id})
        RETURN c.id as id, c.name_ko as name_ko, c.name_en as name_en,
               c.importance as importance, c.concept_type as concept_type
        """

        with self.driver.session() as session:
            result = session.run(query, concept_id=concept_id)
            record = result.single()

            if record:
                return {
                    "id": record["id"],
                    "name_ko": record["name_ko"],
                    "name_en": record["name_en"],
                    "importance": record["importance"],
                    "concept_type": record["concept_type"],
                }
            return None

    def get_intervention_effects(
        self, intervention_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        처방(Intervention)의 효과 조회

        Args:
            intervention_id: resistance_training, protein_intake 등
            limit: 결과 개수

        Returns:
            효과 리스트 (INCREASES, SUPPORTS, REDUCES 관계)
        """
        if not self.driver:
            return []

        query = """
        MATCH (i:Concept {id: $intervention_id})-[r:INCREASES|SUPPORTS|REDUCES]->(target:Concept)
        RETURN target.id as target_id, target.name_ko as target_name_ko,
               target.name_en as target_name_en, type(r) as effect_type,
               r.evidence_level as evidence_level, r.magnitude as magnitude
        ORDER BY r.magnitude DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, intervention_id=intervention_id, limit=limit)
            effects = []
            for record in result:
                effects.append({
                    "target_id": record["target_id"],
                    "target_name_ko": record["target_name_ko"],
                    "target_name_en": record["target_name_en"],
                    "effect_type": record["effect_type"],
                    "evidence_level": record["evidence_level"],
                    "magnitude": record["magnitude"],
                })
            return effects
