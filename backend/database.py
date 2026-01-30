"""
데이터베이스 연결 설정
SQLAlchemy를 사용한 PostgreSQL 연결 관리
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/explainmybody"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    echo=False  # SQL 로그 출력 (필요시 True로 변경)
    #pool_size=5 (default) # 커넥션 풀의 기본 크기
    #max_overflow=10 (default) # 최대 연결 수
)


# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모든 ORM 모델의 부모)
Base = declarative_base()


def get_db():
    """
    데이터베이스 세션 의존성
    FastAPI 엔드포인트에서 Depends(get_db)로 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    데이터베이스 초기화
    모든 테이블 생성
    """
    # 모든 모델 임포트 (테이블 생성을 위해 필요)
    from models import user, health_record, analysis_report, user_detail, weekly_plan
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # # pgvector extension 설치 시도
    # 추후에 pgvector를 사용할 때 필요 
    # (추후에 RAG 사용 시 벡터 DB를 사용하려면, 해당 부분을 다시 활성화시켜야 함)
    # try:
    #     with engine.connect() as conn:
    #         conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    #         conn.commit()
    #         print("✅ pgvector extension 준비 완료")
    # except Exception as e:
    #     print(f"⚠️  pgvector extension을 설치할 수 없습니다: {e}")
