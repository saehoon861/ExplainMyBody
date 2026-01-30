#!/usr/bin/env python3
"""
데이터베이스 테이블 초기화 스크립트
"""
from database import init_db

if __name__ == "__main__":
    print("🔧 데이터베이스 테이블 생성 중...")
    init_db()
    print("✅ 테이블 생성 완료!")
