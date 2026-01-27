# Frontend 설정 가이드

## Node.js 설치 (WSL 환경)

### 방법 1: nvm 사용 (권장)
nvm(Node Version Manager)을 사용하면 여러 Node.js 버전을 쉽게 관리할 수 있습니다.

```bash
# nvm 설치
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 터미널 재시작 또는 설정 적용
source ~/.bashrc

# Node.js LTS 버전 설치
nvm install --lts

# Node.js 버전 확인
node --version
npm --version
```

### 방법 2: apt 사용 (간단)
```bash
# NodeSource 저장소 추가 (최신 버전용)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Node.js 설치
sudo apt-get install -y nodejs

# 버전 확인
node --version
npm --version
```

## Frontend 프로젝트 실행

Node.js 설치 완료 후:

```bash
# frontend 디렉토리로 이동
cd /home/user/ExplainMyBody/frontend_tmp

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

개발 서버는 `http://localhost:5173`에서 실행됩니다.

## 백엔드 연동

프론트엔드가 백엔드 API와 통신하려면 백엔드 서버가 먼저 실행되어야 합니다:

```bash
# 별도 터미널에서
cd /home/user/ExplainMyBody/backend
source ../.venv/bin/activate
python main.py
```

백엔드 서버: `http://localhost:8000`
프론트엔드 서버: `http://localhost:5173`
