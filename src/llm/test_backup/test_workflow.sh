#!/bin/bash
# 워크플로우 테스트 스크립트

echo "======================================"
echo "ExplainMyBody 워크플로우 테스트"
echo "======================================"
echo ""

# 1. 사용자 목록 확인
echo "1. 등록된 사용자 확인..."
python main_workflow.py --list-users
echo ""

# 2. 프로필 목록 확인
echo "2. 샘플 프로필 목록..."
python main_workflow.py --list-profiles
echo ""

# 3. 테스트 실행 (GPT-4o-mini 사용)
echo "3. 워크플로우 실행 (테스트 사용자)..."
python main_workflow.py \
  --username "테스트유저" \
  --email "test@example.com" \
  --profile-id 1 \
  --model gpt-4o-mini

echo ""
echo "======================================"
echo "테스트 완료!"
echo "======================================"
