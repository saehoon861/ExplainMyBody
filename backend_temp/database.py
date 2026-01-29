from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 데이터베이스 엔진 생성
# PostgreSQL 연결 설정
# 형식: postgresql://[user]:[password]@[host]/[dbname]
SQLALCHEMY_DATABASE_URL = "postgresql://myuser:mypassword@localhost/explainmybody"

# PostgreSQL은 check_same_thread 옵션 불필요
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 데이터베이스 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 모델의 기본 클래스
Base = declarative_base()

# 의존성 주입을 위한 DB 세션 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
