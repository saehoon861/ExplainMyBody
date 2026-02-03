"""
RAG 데이터 입력 모듈
JSON 및 Cypher 형식의 논문 데이터를 PostgreSQL에 입력
"""

from .ingest_json import RAGDataIngestion
from .ingest_cypher import CypherDataIngestion

__all__ = [
    'RAGDataIngestion',
    'CypherDataIngestion',
]
