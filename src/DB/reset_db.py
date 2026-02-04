'''

# 데이터베이스 초기화 스크립트

현재 reset_db.py의 위치는 변경되었습니다.


만일 reset_db.py를 실행할 때 오류가 발생한다면, 
해당 파일을 backend/scripts/reset_db.py로 이동시키고, 
그곳에서 실행해주세요.



'''


import sys
import os
import subprocess
from datetime import datetime



# 현재 파일의 부모의 부모 디렉토리(backend)를 sys.path에 추가하여 모듈 임포트 가능하게 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from database import engine, Base, init_db, DATABASE_URL
# 모든 모델을 임포트해야 Base.metadata에 등록됨
# models 폴더에 있는 모든 모델 파일을 임포트합니다.
from models import user, health_record, analysis_report, user_detail, weekly_plan, human_feedback, llm_interaction

def backup_database():
    print("\n📦 데이터베이스 백업 중... (Backing up database)")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backend_dir, f"backup_{timestamp}.sql")
    
    # DATABASE_URL에서 정보 파싱 (기본적인 파싱, 복잡한 URL은 추가 처리 필요할 수 있음)
    # postgresql://user:password@host:port/dbname
    try:
        if "postgresql://" in DATABASE_URL:
            # pg_dump 명령 실행
            # 주의: .env에 비밀번호가 있어도 pg_dump는 PGPASSWORD 환경변수나 .pgpass를 필요로 할 수 있음
            # 여기서는 간단히 실행 시도
            env = os.environ.copy()
            # URL에서 비밀번호 추출하는 로직은 복잡하므로, 로컬 개발 환경 가정하에 실행
            
            command = f"pg_dump {DATABASE_URL} > {backup_file}"
            # shell=True는 보안상 위험할 수 있지만 로컬 스크립트이므로 허용
            subprocess.run(command, shell=True, check=True, env=env)
            print(f"✅ 백업 완료: {backup_file}")
            return True
    except Exception as e:
        print(f"⚠️  백업 실패: {e}")
        print("백업 없이 진행하시겠습니까? (y/n)")
        if input().lower() != 'y':
            return False
            
    return True

def reset_database():
    print("=" * 50)
    print("🛑 데이터베이스 초기화 (Danger Zone) 🛑")
    print("=" * 50)
    print("경고: 이 스크립트를 실행하면 데이터베이스의 '모든 테이블과 데이터'가 영구적으로 삭제됩니다.")
    print("진행하시겠습니까? (데이터 복구 불가능)")
    print("-" * 50)
    
    confirmation = input("확실하다면 'reset' 이라고 입력하세요: ")
    
    if confirmation != 'reset':
        print("\n❌ 입력값이 일치하지 않아 작업을 취소합니다.")
        return

    # 백업 진행
    if not backup_database():
        print("\n❌ 백업 실패 또는 취소로 인해 작업을 중단합니다.")
        return

    print("\n⏳ 기존 테이블 삭제 중... (Dropping tables)")
    try:
        # 외래 키 제약 조건 등으로 인해 순서가 중요할 수 있으나 drop_all이 대부분 처리해줌
        Base.metadata.drop_all(bind=engine)
        print("✅ 테이블 삭제 완료")
    except Exception as e:
        print(f"❌ 테이블 삭제 중 오류 발생: {e}")
        return

    print("\n⏳ 테이블 다시 생성 중... (Recreating tables)")
    try:
        init_db()
        print("✅ 데이터베이스 초기화 완료! (All tables recreated)")
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    reset_database()
