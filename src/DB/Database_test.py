"""
Database Schema and Connection Management
PostgreSQL를 사용한 데이터베이스 관리 (pgvector 지원 준비)

이 모듈은 Data Access Layer (DAL)로서 백엔드 API와 데이터베이스 간의 추상화 계층을 제공합니다.
"""

# ============================================================
# 의존성 임포트 (Dependency Imports)
# ============================================================
import psycopg2  # PostgreSQL 데이터베이스 어댑터 (DB Driver)
import psycopg2.extras  # RealDictCursor 등 확장 기능 제공
import json  # JSONB 데이터 직렬화/역직렬화
import os  # 환경변수 접근
from datetime import datetime  # 타임스탬프 처리
from typing import Optional, Dict, Any, List  # 타입 힌팅
from contextlib import contextmanager  # 컨텍스트 매니저 데코레이터
from dotenv import load_dotenv  # .env 파일에서 환경변수 로드

# 환경변수 로드 (DATABASE_URL 등)
load_dotenv()


# ============================================================
# Database 클래스: Repository Pattern 구현
# ============================================================
# 이 클래스는 Repository Pattern을 따르며, 백엔드 API의 비즈니스 로직과
# 데이터베이스 간의 중간 계층(Persistence Layer)을 담당합니다.
# ============================================================
class Database:
    """PostgreSQL 데이터베이스 관리 클래스"""

    # ============================================================
    # 생성자 (Constructor): 데이터베이스 연결 초기화
    # ============================================================
    # API 서버 시작 시 한 번 호출되어 Database 인스턴스를 생성합니다.
    # 일반적으로 FastAPI/Flask 앱의 startup 이벤트에서 실행됩니다.
    # ============================================================
    def __init__(self, connection_string: Optional[str] = None):
        """
        데이터베이스 연결 문자열을 설정하고 스키마를 초기화합니다.
        
        Args:
            connection_string: PostgreSQL 연결 문자열
                예: "postgresql://user:password@localhost:5432/dbname"
                None인 경우 환경변수에서 읽음
                
        API 연결 지점:
            - FastAPI: @app.on_event("startup")에서 호출
            - Flask: app.before_first_request에서 호출
            - 싱글톤 패턴으로 앱 전체에서 하나의 인스턴스 공유
        """
        if connection_string:
            self.connection_string = connection_string
        else:
            # 환경변수에서 연결 정보 읽기 (12-Factor App 원칙)
            # DATABASE_URL은 .env 파일 또는 시스템 환경변수에서 로드
            self.connection_string = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/explainmybody"
            )

        # 데이터베이스 스키마 초기화 (테이블 생성, 인덱스 생성 등)
        self._init_database()

    # ============================================================
    # 컨텍스트 매니저 (Context Manager): 연결 관리
    # ============================================================
    # 이 메서드는 데이터베이스 연결의 생명주기를 관리합니다.
    # API 요청당 하나의 연결을 생성하고, 트랜잭션을 관리합니다.
    # ============================================================
    @contextmanager
    def get_connection(self):
        """
        데이터베이스 연결 컨텍스트 매니저 (Connection Pool 역할)
        
        트랜잭션 관리 (ACID 보장):
            1. 연결 생성 (Connection Acquisition)
            2. 자동 커밋 비활성화 (Explicit Transaction)
            3. 성공 시 커밋 (Commit)
            4. 실패 시 롤백 (Rollback)
            5. 연결 종료 (Connection Release)
            
        API 연결 지점:
            - 모든 데이터베이스 메서드 내부에서 사용
            - API 엔드포인트 핸들러에서 간접적으로 호출
            - 예: POST /api/users -> create_user() -> get_connection()
            
        사용 예시:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        # 1. 데이터베이스 연결 생성 (TCP 소켓 연결)
        conn = psycopg2.connect(self.connection_string)
        
        # 2. 명시적 트랜잭션 모드 설정 (autocommit=False)
        # 이를 통해 여러 쿼리를 하나의 원자적 작업으로 묶을 수 있음
        conn.set_session(autocommit=False)
        
        try:
            # 3. 연결 객체를 호출자에게 전달 (yield)
            yield conn
            
            # 4. 정상 실행 시 트랜잭션 커밋 (데이터베이스에 변경사항 반영)
            conn.commit()
        except Exception as e:
            # 5. 예외 발생 시 롤백 (변경사항 취소, 데이터 일관성 유지)
            conn.rollback()
            
            # 6. 예외를 상위 레이어(API 핸들러)로 전파
            raise e
        finally:
            # 7. 연결 종료 (리소스 해제)
            # 성공/실패 여부와 관계없이 항상 실행
            conn.close()


    # ============================================================
    # 스키마 초기화 (Schema Initialization): DDL 실행
    # ============================================================
    # 애플리케이션 시작 시 자동으로 데이터베이스 스키마를 생성합니다.
    # 이는 Migration Tool (Alembic, Flyway 등)의 간소화된 버전입니다.
    # ============================================================
    def _init_database(self):
        """
        데이터베이스 초기화 및 테이블 생성 (DDL 실행)
        
        실행 시점:
            - __init__() 메서드에서 자동 호출
            - 애플리케이션 시작 시 한 번만 실행
            
        역할:
            1. PostgreSQL Extension 설치 (pgvector)
            2. 테이블 스키마 생성 (CREATE TABLE IF NOT EXISTS)
            3. 인덱스 생성 (성능 최적화)
            
        API 연결 지점:
            - 직접적인 API 호출 없음
            - 앱 시작 시 자동 실행되어 데이터베이스 준비 상태 보장
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # ========================================================
            # 1. PostgreSQL Extension 설치
            # ========================================================
            # pgvector: 벡터 유사도 검색을 위한 확장 (향후 RAG, 임베딩 검색에 사용)
            # ========================================================
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                print("✅ pgvector extension 준비 완료")
            except Exception as e:
                print(f"⚠️  pgvector extension을 설치할 수 없습니다: {e}")
                print("   (나중에 pgvector가 필요할 때 수동으로 설치하세요)")

            # ========================================================
            # 2. 테이블 스키마 정의 (Entity-Relationship Model)
            # ========================================================
            
            # --------------------------------------------------------
            # 2-1. users 테이블: 사용자 정보 (User Entity)
            # --------------------------------------------------------
            # API 연결: POST /api/auth/register, GET /api/users/:id
            # --------------------------------------------------------
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,              -- 자동 증가 기본키 (Auto-increment PK)
                    username VARCHAR(255) NOT NULL,     -- 사용자 이름
                    email VARCHAR(255) UNIQUE NOT NULL, -- 이메일 (Unique Constraint로 중복 방지)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 생성 시각
                )
            """)

            # --------------------------------------------------------
            # 2-2. user_goals 테이블: 사용자 목표 (Goal Entity)
            # --------------------------------------------------------
            # API 연결: POST /api/goals, GET /api/users/:id/goals
            # Foreign Key로 users 테이블과 1:N 관계 형성
            # --------------------------------------------------------
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_goals (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- 외래키 (FK), 사용자 삭제 시 목표도 삭제
                    goal_type VARCHAR(255),             -- 목표 유형 (예: 체중 감량, 근육 증가)
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 목표 시작 시각
                    ended_at TIMESTAMP                  -- 목표 종료 시각 (NULL이면 진행 중)
                )
            """)

            # --------------------------------------------------------
            # 2-3. health_records 테이블: 건강 기록 (Health Record Entity)
            # --------------------------------------------------------
            # API 연결: POST /api/health-records, GET /api/health-records/:id
            # JSONB 타입 사용으로 스키마리스 데이터 저장 (NoSQL 특성)
            # --------------------------------------------------------
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- 외래키
                    source VARCHAR(100) DEFAULT 'manual',  -- 데이터 출처 (manual, api, device 등)
                    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 측정 시각
                    measurements JSONB NOT NULL,        -- 건강 측정 데이터 (JSONB로 유연한 스키마)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 레코드 생성 시각
                )
            """)

            # --------------------------------------------------------
            # 2-4. analysis_reports 테이블: AI 분석 리포트 (Report Entity)
            # --------------------------------------------------------
            # API 연결: POST /api/analysis, GET /api/reports/:id
            # LLM 출력 결과를 저장하는 테이블
            # --------------------------------------------------------
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- 외래키
                    record_id INTEGER NOT NULL REFERENCES health_records(id) ON DELETE CASCADE,  -- 분석 대상 레코드
                    llm_output TEXT NOT NULL,           -- LLM 생성 텍스트 (분석 결과)
                    model_version VARCHAR(100),         -- 사용된 모델 버전 (예: gpt-4, claude-3)
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 생성 시각
                )
            """)

            # ========================================================
            # 3. 인덱스 생성 (Query Performance Optimization)
            # ========================================================
            # 인덱스는 SELECT 쿼리 성능을 향상시키지만, INSERT/UPDATE 성능은 저하
            # 자주 조회되는 컬럼에 대해서만 생성
            # ========================================================
            
            # --------------------------------------------------------
            # 3-1. Composite Index: user_id + measured_at (내림차순)
            # --------------------------------------------------------
            # 사용 쿼리: SELECT * FROM health_records WHERE user_id = ? ORDER BY measured_at DESC
            # API 연결: GET /api/users/:id/health-records (최근 기록 조회)
            # --------------------------------------------------------
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_records_user_measured
                ON health_records(user_id, measured_at DESC)
            """)

            # --------------------------------------------------------
            # 3-2. Single Column Index: user_id
            # --------------------------------------------------------
            # 사용 쿼리: SELECT * FROM health_records WHERE user_id = ?
            # API 연결: GET /api/users/:id/health-records (모든 기록 조회)
            # --------------------------------------------------------
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_records_user
                ON health_records(user_id)
            """)

            # --------------------------------------------------------
            # 3-3. GIN Index: JSONB 필드 (Generalized Inverted Index)
            # --------------------------------------------------------
            # JSONB 필드 내부 키-값 검색 성능 향상
            # 사용 쿼리: SELECT * FROM health_records WHERE measurements @> '{"key": "value"}'
            # API 연결: GET /api/health-records?filter={"stage2_근육보정체형": "근육형"}
            # --------------------------------------------------------
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_records_measurements_gin
                ON health_records USING GIN (measurements)
            """)

            print("✅ PostgreSQL 데이터베이스 초기화 완료")


    # ============================================================
    # User CRUD Operations (Create, Read, Update, Delete)
    # ============================================================
    # 사용자 엔티티에 대한 데이터베이스 작업을 수행합니다.
    # Repository Pattern의 핵심 메서드들입니다.
    # ============================================================

    def create_user(self, username: str, email: str) -> int:
        """
        새 사용자 생성 (INSERT 작업)
        
        Args:
            username: 사용자 이름
            email: 이메일 주소 (UNIQUE 제약조건)
            
        Returns:
            생성된 사용자의 ID (Primary Key)
            
        API 연결 지점:
            - POST /api/auth/register
            - POST /api/users
            
        요청 흐름:
            1. API 핸들러가 요청 바디에서 username, email 추출
            2. 이 메서드 호출하여 DB에 INSERT
            3. 생성된 user_id를 응답으로 반환
            
        SQL 패턴:
            - Parameterized Query (%s)로 SQL Injection 방지
            - RETURNING 절로 생성된 ID를 한 번에 가져옴
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Parameterized Query: SQL Injection 방지
            # RETURNING id: INSERT 후 생성된 ID를 즉시 반환
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
                (username, email)  # 파라미터 바인딩
            )
            
            # fetchone()[0]: 첫 번째 행의 첫 번째 컬럼 (id) 추출
            user_id = cursor.fetchone()[0]
            return user_id

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        이메일로 사용자 조회 (SELECT 작업)
        
        Args:
            email: 조회할 이메일 주소
            
        Returns:
            사용자 정보 딕셔너리 또는 None
            예: {'id': 1, 'username': 'John', 'email': 'john@example.com', 'created_at': ...}
            
        API 연결 지점:
            - POST /api/auth/login (이메일로 사용자 존재 확인)
            - GET /api/users?email=xxx
            
        요청 흐름:
            1. API 핸들러가 쿼리 파라미터 또는 바디에서 email 추출
            2. 이 메서드 호출하여 DB에서 SELECT
            3. 사용자 정보를 JSON으로 응답
            
        특징:
            - RealDictCursor: 결과를 딕셔너리로 반환 (컬럼명이 키가 됨)
            - ORM 없이 딕셔너리로 직접 매핑
        """
        with self.get_connection() as conn:
            # RealDictCursor: 결과를 Row 객체 대신 딕셔너리로 반환
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # WHERE 절에 Parameterized Query 사용
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            # fetchone(): 단일 행 조회 (없으면 None 반환)
            row = cursor.fetchone()
            
            # RealDictRow를 일반 dict로 변환하여 반환
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        ID로 사용자 조회 (SELECT 작업)
        
        Args:
            user_id: 조회할 사용자 ID (Primary Key)
            
        Returns:
            사용자 정보 딕셔너리 또는 None
            
        API 연결 지점:
            - GET /api/users/:id
            - GET /api/users/:id/profile
            
        요청 흐름:
            1. API 핸들러가 경로 파라미터에서 user_id 추출
            2. 이 메서드 호출하여 DB에서 SELECT
            3. 사용자 정보를 JSON으로 응답 (없으면 404 에러)
            
        특징:
            - Primary Key 조회로 매우 빠른 성능 (인덱스 자동 사용)
            - get_user_by_email과 동일한 패턴, 조회 조건만 다름
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Primary Key로 조회 (가장 빠른 조회 방법)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ============================================================
    # Health Records CRUD Operations
    # ============================================================
    # 건강 기록 데이터를 관리합니다.
    # JSONB 타입을 사용하여 유연한 스키마를 지원합니다.
    # ============================================================

    def save_health_record(
        self,
        user_id: int,
        measurements: Dict[str, Any],
        source: str = "manual",
        measured_at: Optional[str] = None
    ) -> int:
        """
        건강 기록 저장 (INSERT 작업 with JSONB)
        
        Args:
            user_id: 사용자 ID (Foreign Key)
            measurements: 건강 측정 데이터 (Python dict)
                예: {
                    "stage1_체형": "근육형",
                    "stage2_근육보정체형": "근육형",
                    "BMI": 23.5,
                    "체지방률": 18.2
                }
            source: 데이터 출처 (manual, api, device 등)
            measured_at: 측정 시각 (ISO 8601 형식, None이면 현재 시각)
            
        Returns:
            생성된 건강 기록의 ID
            
        API 연결 지점:
            - POST /api/health-records
            - POST /api/users/:id/health-records
            
        요청 흐름:
            1. API 핸들러가 요청 바디에서 measurements 추출
            2. 이 메서드 호출하여 JSONB로 직렬화 후 INSERT
            3. 생성된 record_id를 응답으로 반환
            
        JSONB 사용 이유:
            - 스키마 유연성: 측정 항목이 추가/변경되어도 테이블 변경 불필요
            - 인덱싱 가능: GIN 인덱스로 JSONB 내부 검색 가능
            - 타입 보존: JSON과 달리 PostgreSQL 네이티브 타입으로 저장
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Python dict를 JSON 문자열로 직렬화
            # ensure_ascii=False: 한글 등 유니코드 문자를 그대로 저장
            measurements_json = json.dumps(measurements, ensure_ascii=False)

            # 측정 시각이 제공된 경우와 아닌 경우를 분기 처리
            if measured_at:
                cursor.execute(
                    """INSERT INTO health_records
                       (user_id, source, measured_at, measurements)
                       VALUES (%s, %s, %s, %s::jsonb)
                       RETURNING id""",
                    (user_id, source, measured_at, measurements_json)
                )
            else:
                # measured_at 미제공 시 DEFAULT CURRENT_TIMESTAMP 사용
                cursor.execute(
                    """INSERT INTO health_records
                       (user_id, source, measurements)
                       VALUES (%s, %s, %s::jsonb)
                       RETURNING id""",
                    (user_id, source, measurements_json)
                )

            # 생성된 레코드 ID 반환
            record_id = cursor.fetchone()[0]
            return record_id

    def get_health_record(self, record_id: int) -> Optional[Dict]:
        """
        건강 기록 조회 (SELECT 작업)
        
        Args:
            record_id: 조회할 건강 기록 ID
            
        Returns:
            건강 기록 딕셔너리 (measurements는 자동으로 dict로 역직렬화됨)
            예: {
                'id': 1,
                'user_id': 1,
                'source': 'manual',
                'measured_at': datetime(...),
                'measurements': {'stage1_체형': '근육형', ...},
                'created_at': datetime(...)
            }
            
        API 연결 지점:
            - GET /api/health-records/:id
            - GET /api/analysis/:record_id (분석 전 데이터 조회)
            
        요청 흐름:
            1. API 핸들러가 경로 파라미터에서 record_id 추출
            2. 이 메서드 호출하여 DB에서 SELECT
            3. 건강 기록을 JSON으로 응답
            
        특징:
            - psycopg2가 JSONB를 자동으로 Python dict로 변환
            - 별도의 역직렬화 코드 불필요
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM health_records WHERE id = %s", (record_id,))
            row = cursor.fetchone()

            if row:
                record = dict(row)
                # JSONB는 psycopg2에 의해 이미 Python dict로 자동 변환됨
                # 추가 처리 없이 그대로 반환
                return record
            return None

    def get_user_health_records(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        사용자의 건강 기록 목록 조회 (SELECT with Pagination)
        
        Args:
            user_id: 조회할 사용자 ID
            limit: 조회할 최대 레코드 수 (기본값: 10)
            
        Returns:
            건강 기록 리스트 (최신순 정렬)
            
        API 연결 지점:
            - GET /api/users/:id/health-records
            - GET /api/users/:id/health-records?limit=20
            
        요청 흐름:
            1. API 핸들러가 경로 파라미터와 쿼리 파라미터 추출
            2. 이 메서드 호출하여 최근 기록 조회
            3. 기록 리스트를 JSON 배열로 응답
            
        성능 최적화:
            - ORDER BY measured_at DESC: 복합 인덱스 활용
            - LIMIT: 페이지네이션으로 대량 데이터 조회 방지
            - idx_health_records_user_measured 인덱스 자동 사용
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 최신순 정렬 + 페이지네이션
            cursor.execute(
                """SELECT * FROM health_records
                   WHERE user_id = %s
                   ORDER BY measured_at DESC
                   LIMIT %s""",
                (user_id, limit)
            )
            
            # fetchall(): 모든 결과 행을 리스트로 반환
            rows = cursor.fetchall()
            
            # RealDictRow 리스트를 일반 dict 리스트로 변환
            return [dict(row) for row in rows]

    def search_health_records_by_measurement(
        self,
        user_id: int,
        key: str,
        value: Any
    ) -> List[Dict]:
        """
        JSONB 필드 내 특정 값으로 검색 (PostgreSQL JSONB Operator 활용)
        
        Args:
            user_id: 사용자 ID
            key: JSONB 내부 키 (예: 'stage2_근육보정체형')
            value: 검색할 값 (예: '근육형')
            
        Returns:
            조건에 맞는 건강 기록 리스트
            
        API 연결 지점:
            - GET /api/health-records?user_id=1&filter[stage2_근육보정체형]=근육형
            - GET /api/users/:id/health-records/search
            
        요청 흐름:
            1. API 핸들러가 쿼리 파라미터에서 필터 조건 추출
            2. 이 메서드 호출하여 JSONB 내부 검색
            3. 필터링된 기록 리스트를 응답
            
        JSONB Operator 설명:
            - measurements->>key: JSONB에서 key의 값을 텍스트로 추출
            - ->> 연산자는 GIN 인덱스를 활용하여 빠른 검색 가능
            
        사용 예시:
            search_health_records_by_measurement(1, 'stage2_근육보정체형', '근육형')
            -> measurements에 {'stage2_근육보정체형': '근육형'}을 포함하는 모든 레코드 반환
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # JSONB 연산자 ->>: JSON 객체에서 키의 값을 텍스트로 추출
            # GIN 인덱스 (idx_health_records_measurements_gin) 활용
            cursor.execute(
                """SELECT * FROM health_records
                   WHERE user_id = %s
                   AND measurements->>%s = %s
                   ORDER BY measured_at DESC""",
                (user_id, key, str(value))  # value를 문자열로 변환하여 비교
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ============================================================
    # Analysis Reports CRUD Operations
    # ============================================================
    # AI/LLM 분석 결과를 저장하고 조회합니다.
    # 건강 기록과 1:1 또는 1:N 관계를 형성합니다.
    # ============================================================

    def save_analysis_report(
        self,
        user_id: int,
        record_id: int,
        llm_output: str,
        model_version: str
    ) -> int:
        """
        분석 리포트 저장 (INSERT 작업)
        
        Args:
            user_id: 사용자 ID (Foreign Key)
            record_id: 분석 대상 건강 기록 ID (Foreign Key)
            llm_output: LLM이 생성한 분석 텍스트 (마크다운, HTML 등)
            model_version: 사용된 LLM 모델 버전 (예: 'gpt-4-turbo', 'claude-3-opus')
            
        Returns:
            생성된 리포트의 ID
            
        API 연결 지점:
            - POST /api/analysis
            - POST /api/health-records/:id/analyze
            
        요청 흐름 (전체 분석 파이프라인):
            1. 클라이언트가 POST /api/analysis 요청 (건강 데이터 포함)
            2. API 핸들러가 save_health_record() 호출하여 데이터 저장
            3. API 핸들러가 LLM API 호출 (예: OpenAI, Anthropic)
            4. LLM 응답을 받아 이 메서드로 저장
            5. 리포트 ID를 클라이언트에 반환
            
        사용 예시:
            # LLM 분석 후
            report_id = db.save_analysis_report(
                user_id=1,
                record_id=123,
                llm_output="# 분석 결과\n\n당신의 체형은...",
                model_version="gpt-4-turbo-2024-04-09"
            )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # LLM 출력을 TEXT 타입으로 저장 (긴 텍스트 지원)
            cursor.execute(
                """INSERT INTO analysis_reports
                   (user_id, record_id, llm_output, model_version)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id""",
                (user_id, record_id, llm_output, model_version)
            )
            
            # 생성된 리포트 ID 반환
            report_id = cursor.fetchone()[0]
            return report_id

    def get_analysis_report(self, report_id: int) -> Optional[Dict]:
        """
        분석 리포트 조회 (SELECT 작업)
        
        Args:
            report_id: 조회할 리포트 ID
            
        Returns:
            리포트 딕셔너리 (llm_output 포함)
            
        API 연결 지점:
            - GET /api/reports/:id
            - GET /api/analysis/reports/:id
            
        요청 흐름:
            1. 클라이언트가 리포트 ID로 조회 요청
            2. 이 메서드로 DB에서 리포트 조회
            3. LLM 출력을 포함한 리포트를 JSON으로 응답
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM analysis_reports WHERE id = %s", (report_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_report_by_record_id(self, record_id: int) -> Optional[Dict]:
        """
        건강 기록 ID로 리포트 조회 (SELECT 작업)
        
        Args:
            record_id: 건강 기록 ID
            
        Returns:
            해당 기록에 대한 가장 최근 리포트 (없으면 None)
            
        API 연결 지점:
            - GET /api/health-records/:id/report
            - GET /api/health-records/:id/latest-analysis
            
        요청 흐름:
            1. 클라이언트가 건강 기록에 대한 분석 결과 요청
            2. 이 메서드로 해당 기록의 분석 리포트 조회
            3. 가장 최근 리포트를 응답 (여러 번 분석한 경우 최신 것)
            
        특징:
            - 하나의 건강 기록에 대해 여러 분석 가능 (재분석 지원)
            - ORDER BY generated_at DESC: 가장 최근 분석 결과 반환
            - LIMIT 1: 하나만 반환
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 가장 최근 리포트 조회 (재분석 시 최신 버전 반환)
            cursor.execute(
                """SELECT * FROM analysis_reports
                   WHERE record_id = %s
                   ORDER BY generated_at DESC
                   LIMIT 1""",
                (record_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # ============================================================
    # User Goals CRUD Operations
    # ============================================================
    # 사용자의 건강 목표를 관리합니다.
    # 목표 설정, 진행 상황 추적, 종료 처리를 지원합니다.
    # ============================================================

    def create_user_goal(self, user_id: int, goal_type: str) -> int:
        """
        사용자 목표 생성 (INSERT 작업)
        
        Args:
            user_id: 사용자 ID
            goal_type: 목표 유형 (예: '체중 감량', '근육 증가', '체지방 감소')
            
        Returns:
            생성된 목표 ID
            
        API 연결 지점:
            - POST /api/goals
            - POST /api/users/:id/goals
            
        요청 흐름:
            1. 클라이언트가 목표 설정 요청
            2. 이 메서드로 목표 생성 (started_at은 자동 설정)
            3. 목표 ID를 반환하여 클라이언트에 응답
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # started_at은 DEFAULT CURRENT_TIMESTAMP로 자동 설정
            # ended_at은 NULL (목표 진행 중)
            cursor.execute(
                "INSERT INTO user_goals (user_id, goal_type) VALUES (%s, %s) RETURNING id",
                (user_id, goal_type)
            )
            goal_id = cursor.fetchone()[0]
            return goal_id

    def get_active_user_goals(self, user_id: int) -> List[Dict]:
        """
        활성 사용자 목표 조회 (SELECT 작업)
        
        Args:
            user_id: 조회할 사용자 ID
            
        Returns:
            활성 목표 리스트 (ended_at이 NULL인 목표들)
            
        API 연결 지점:
            - GET /api/users/:id/goals
            - GET /api/users/:id/active-goals
            
        요청 흐름:
            1. 클라이언트가 현재 진행 중인 목표 조회 요청
            2. 이 메서드로 ended_at이 NULL인 목표들 조회
            3. 활성 목표 리스트를 응답
            
        특징:
            - ended_at IS NULL: 종료되지 않은 목표만 조회
            - 목표 종료 시 UPDATE user_goals SET ended_at = NOW() WHERE id = ?
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # ended_at이 NULL인 목표만 조회 (진행 중인 목표)
            cursor.execute(
                "SELECT * FROM user_goals WHERE user_id = %s AND ended_at IS NULL",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ============================================================
    # Utility Methods (유틸리티 메서드)
    # ============================================================
    # 데이터베이스 상태 확인, 통계 조회 등 보조 기능을 제공합니다.
    # ============================================================

    def test_connection(self) -> bool:
        """
        데이터베이스 연결 테스트 (Health Check)
        
        Returns:
            연결 성공 시 True, 실패 시 False
            
        API 연결 지점:
            - GET /api/health
            - GET /api/status
            
        사용 목적:
            1. 애플리케이션 시작 시 DB 연결 확인
            2. Health Check 엔드포인트에서 시스템 상태 모니터링
            3. 배포 전 연결 테스트
            
        요청 흐름:
            1. 모니터링 시스템이나 로드밸런서가 /api/health 호출
            2. API 핸들러가 이 메서드로 DB 연결 상태 확인
            3. 성공/실패 여부를 응답에 포함
            
        특징:
            - SELECT 1: 가장 가벼운 쿼리로 연결만 테스트
            - 예외 처리로 연결 실패 시에도 안전하게 False 반환
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 최소한의 쿼리로 연결 테스트
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False

    def get_user_statistics(self, user_id: int) -> Dict[str, int]:
        """
        사용자 통계 조회 (Analytics Query)
        
        Args:
            user_id: 통계를 조회할 사용자 ID
            
        Returns:
            통계 딕셔너리 {'total_records': int, 'total_reports': int}
            
        API 연결 지점:
            - GET /api/users/:id/statistics
            - GET /api/users/:id/dashboard
            
        요청 흐름:
            1. 클라이언트가 대시보드 또는 프로필 페이지 요청
            2. API 핸들러가 이 메서드로 사용자 활동 통계 조회
            3. 통계 데이터를 JSON으로 응답하여 UI에 표시
            
        사용 예시:
            stats = db.get_user_statistics(user_id=1)
            # {'total_records': 25, 'total_reports': 25}
            
        확장 가능성:
            - 추가 통계: 평균 BMI, 체중 변화 추이, 목표 달성률 등
            - 집계 함수: AVG(), MAX(), MIN() 등 활용
            - 시계열 분석: 주간/월간 통계
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # --------------------------------------------------------
            # 1. 건강 기록 수 집계 (COUNT Aggregation)
            # --------------------------------------------------------
            cursor.execute(
                "SELECT COUNT(*) FROM health_records WHERE user_id = %s",
                (user_id,)
            )
            record_count = cursor.fetchone()[0]

            # --------------------------------------------------------
            # 2. 분석 리포트 수 집계 (COUNT Aggregation)
            # --------------------------------------------------------
            cursor.execute(
                "SELECT COUNT(*) FROM analysis_reports WHERE user_id = %s",
                (user_id,)
            )
            report_count = cursor.fetchone()[0]

            # 통계 딕셔너리 반환 (JSON 직렬화 가능)
            return {
                "total_records": record_count,
                "total_reports": report_count
            }


# ============================================================
# 모듈 사용 예시 (Example Usage)
# ============================================================
"""
# 1. Database 인스턴스 생성 (애플리케이션 시작 시)
db = Database()

# 2. 사용자 생성 (회원가입)
user_id = db.create_user(username="홍길동", email="hong@example.com")

# 3. 건강 기록 저장 (데이터 입력)
record_id = db.save_health_record(
    user_id=user_id,
    measurements={
        "stage1_체형": "근육형",
        "BMI": 23.5,
        "체지방률": 18.2
    },
    source="manual"
)

# 4. LLM 분석 후 리포트 저장
report_id = db.save_analysis_report(
    user_id=user_id,
    record_id=record_id,
    llm_output="# 분석 결과\n\n당신의 체형은 근육형입니다...",
    model_version="gpt-4-turbo"
)

# 5. 데이터 조회
user = db.get_user_by_id(user_id)
records = db.get_user_health_records(user_id, limit=10)
report = db.get_report_by_record_id(record_id)
stats = db.get_user_statistics(user_id)

# 6. JSONB 검색
muscle_records = db.search_health_records_by_measurement(
    user_id=user_id,
    key="stage1_체형",
    value="근육형"
)
"""
