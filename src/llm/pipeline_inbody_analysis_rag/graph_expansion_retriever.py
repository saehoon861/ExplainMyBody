"""
Graph Expansion Retriever
- SQL Hop 기반 자동 확장: Seed → Risk → Intervention
- LLM reasoning 없이 Graph 구조로 자동 추론
- Step A: Seed → Papers
- Step B: Papers → Risk/Outcome Concepts
- Step C: Papers → Intervention Concepts
- Step D: Evidence Chunks 반환
"""

from typing import List, Dict, Optional
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class GraphExpansionRetriever:
    """
    Graph Hop 기반 Concept 확장 및 Evidence 검색

    Flow:
    Seed Concepts → Papers → Risk Concepts → Intervention Concepts → Evidence Chunks
    """

    def __init__(
        self,
        db_url: Optional[str] = None
    ):
        """
        Args:
            db_url: PostgreSQL 연결 URL (없으면 환경변수에서)
        """
        if not db_url:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL이 설정되지 않았습니다.")

        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def expand_and_retrieve(
        self,
        seed_concept_ids: List[str],
        top_k_papers: int = 20,
        top_k_risks: int = 10,
        top_k_interventions: int = 10,
        top_k_evidence: int = 5
    ) -> Dict[str, any]:
        """
        Graph Expansion: Seed → Risk → Intervention → Evidence

        Args:
            seed_concept_ids: Seed concept ID 리스트
            top_k_papers: Seed와 연결된 논문 수
            top_k_risks: 확장할 Risk concept 수
            top_k_interventions: 확장할 Intervention concept 수
            top_k_evidence: 최종 반환할 Evidence chunk 수

        Returns:
            {
                "seed_papers": [...],
                "risk_concepts": [...],
                "intervention_concepts": [...],
                "evidence_chunks": [...]
            }
        """
        session = self.SessionLocal()

        try:
            # Step A: Seed → Papers
            seed_papers = self._get_seed_papers(session, seed_concept_ids, top_k_papers)

            # Step B: Papers → Risk Concepts
            risk_concepts = self._get_risk_concepts(session, seed_papers, top_k_risks)

            # Step C: Papers → Intervention Concepts
            intervention_concepts = self._get_intervention_concepts(
                session, seed_papers, top_k_interventions
            )

            # Step D: Evidence Chunks
            evidence_chunks = self._get_evidence_chunks(
                session,
                seed_papers,
                risk_concepts,
                intervention_concepts,
                top_k_evidence
            )

            return {
                "seed_papers": seed_papers,
                "risk_concepts": risk_concepts,
                "intervention_concepts": intervention_concepts,
                "evidence_chunks": evidence_chunks
            }

        finally:
            session.close()

    def _get_seed_papers(
        self,
        session,
        seed_concept_ids: List[str],
        top_k: int
    ) -> List[int]:
        """
        Step A: Seed Concept과 연결된 Paper 찾기

        SQL:
        SELECT DISTINCT paper_id
        FROM paper_concept_relations
        WHERE concept_id = ANY(:seed_concepts)
        LIMIT :top_k;
        """
        query = text("""
            SELECT DISTINCT paper_id
            FROM paper_concept_relations
            WHERE concept_id = ANY(:seed_concepts)
            LIMIT :top_k
        """)

        result = session.execute(
            query,
            {"seed_concepts": seed_concept_ids, "top_k": top_k}
        )

        paper_ids = [row[0] for row in result]

        print(f"  📄 Step A: Seed → Papers: {len(paper_ids)}개 논문 발견")

        return paper_ids

    def _get_risk_concepts(
        self,
        session,
        paper_ids: List[int],
        top_k: int
    ) -> List[Dict[str, any]]:
        """
        Step B: 같은 Paper에 있는 Risk/Outcome Concept 확장

        SQL:
        SELECT DISTINCT
            concept_id,
            concept_name_ko,
            confidence,
            evidence_level,
            COUNT(DISTINCT paper_id) as paper_count
        FROM paper_concept_relations
        WHERE paper_id = ANY(:paper_ids)
          AND concept_type = 'Outcome'
        GROUP BY concept_id, concept_name_ko, confidence, evidence_level
        ORDER BY
            CASE evidence_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            paper_count DESC,
            confidence DESC
        LIMIT :top_k;
        """
        if not paper_ids:
            return []

        query = text("""
            SELECT DISTINCT
                concept_id,
                COUNT(DISTINCT paper_id) as paper_count,
                AVG(confidence) as avg_confidence
            FROM paper_concept_relations
            WHERE paper_id = ANY(:paper_ids)
            GROUP BY concept_id
            ORDER BY paper_count DESC, avg_confidence DESC
            LIMIT :top_k
        """)

        result = session.execute(
            query,
            {"paper_ids": paper_ids, "top_k": top_k}
        )

        risk_concepts = []
        for row in result:
            risk_concepts.append({
                "concept_id": row[0],
                "paper_count": row[1],
                "avg_confidence": float(row[2]) if row[2] else 0.0
            })

        print(f"  🎯 Step B: Papers → Risk Concepts: {len(risk_concepts)}개 위험 요소 확장")

        return risk_concepts

    def _get_intervention_concepts(
        self,
        session,
        paper_ids: List[int],
        top_k: int
    ) -> List[Dict[str, any]]:
        """
        Step C: 같은 Paper에 있는 Intervention Concept 확장

        SQL:
        SELECT DISTINCT
            concept_id,
            concept_name_ko,
            relation_type,
            confidence,
            evidence_level,
            COUNT(DISTINCT paper_id) as paper_count
        FROM paper_concept_relations
        WHERE paper_id = ANY(:paper_ids)
          AND concept_type = 'Intervention'
        GROUP BY concept_id, concept_name_ko, relation_type, confidence, evidence_level
        ORDER BY
            CASE evidence_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            paper_count DESC,
            confidence DESC
        LIMIT :top_k;
        """
        if not paper_ids:
            return []

        query = text("""
            SELECT DISTINCT
                concept_id,
                COUNT(DISTINCT paper_id) as paper_count,
                AVG(confidence) as avg_confidence
            FROM paper_concept_relations
            WHERE paper_id = ANY(:paper_ids)
            GROUP BY concept_id
            ORDER BY paper_count DESC, avg_confidence DESC
            LIMIT :top_k
        """)

        result = session.execute(
            query,
            {"paper_ids": paper_ids, "top_k": top_k}
        )

        intervention_concepts = []
        for row in result:
            intervention_concepts.append({
                "concept_id": row[0],
                "paper_count": row[1],
                "avg_confidence": float(row[2]) if row[2] else 0.0
            })

        print(f"  💊 Step C: Papers → Intervention Concepts: {len(intervention_concepts)}개 처방 발견")

        return intervention_concepts

    def _get_evidence_chunks(
        self,
        session,
        paper_ids: List[int],
        risk_concepts: List[Dict[str, any]],
        intervention_concepts: List[Dict[str, any]],
        top_k: int
    ) -> List[Dict[str, any]]:
        """
        Step D: 최종 Evidence Chunk까지 반환

        SQL:
        SELECT
            pn.id,
            pn.paper_id,
            pn.title,
            pn.chunk_text,
            pn.chunk_ko_summary,
            pn.year,
            pn.source,
            pcr.concept_id,
            pcr.confidence,
            pcr.evidence_level
        FROM paper_nodes pn
        JOIN paper_concept_relations pcr ON pn.id = pcr.paper_id
        WHERE pn.id = ANY(:paper_ids)
          AND (
            pcr.concept_id = ANY(:risk_concept_ids) OR
            pcr.concept_id = ANY(:intervention_concept_ids)
          )
        ORDER BY
            CASE pcr.evidence_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            pcr.confidence DESC
        LIMIT :top_k;
        """
        if not paper_ids:
            return []

        risk_concept_ids = [r["concept_id"] for r in risk_concepts]
        intervention_concept_ids = [i["concept_id"] for i in intervention_concepts]

        all_concept_ids = risk_concept_ids + intervention_concept_ids

        if not all_concept_ids:
            all_concept_ids = ["dummy"]  # Fallback

        query = text("""
            SELECT
                pn.id,
                pn.paper_id,
                pn.title,
                pn.chunk_text,
                pn.chunk_ko_summary,
                pn.year,
                pn.source,
                pcr.concept_id
            FROM paper_nodes pn
            JOIN paper_concept_relations pcr ON pn.id = pcr.paper_id
            WHERE pn.id = ANY(:paper_ids)
              AND pcr.concept_id = ANY(:concept_ids)
            ORDER BY pn.id DESC
            LIMIT :top_k
        """)

        result = session.execute(
            query,
            {
                "paper_ids": paper_ids,
                "concept_ids": all_concept_ids,
                "top_k": top_k
            }
        )

        evidence_chunks = []
        for row in result:
            evidence_chunks.append({
                "id": row[0],
                "paper_id": row[1],
                "title": row[2] or "N/A",
                "chunk_text": row[3] or "",
                "chunk_ko_summary": row[4] or "",
                "year": row[5],
                "source": row[6] or "Unknown",
                "concept_id": row[7],
                "evidence": (row[4] or row[3])[:500]  # 한글 요약 우선, 없으면 원문
            })

        print(f"  📚 Step D: Evidence Chunks: {len(evidence_chunks)}개 근거 반환")

        return evidence_chunks
