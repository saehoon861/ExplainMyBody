# [Inference]: Kakao 로그인 예시 로직
from fastapi import FastAPI, Depends
import httpx

app = FastAPI()

@app.get("/auth/kakao/callback")
async def kakao_callback(code: str):
    # 1. 인가 코드로 토큰 요청
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "YOUR_CLIENT_ID",
                "redirect_uri": "http://localhost:8000/auth/kakao/callback",
                "code": code
            }
        )
        access_token = token_response.json().get("access_token")
        
        # 2. 토큰으로 사용자 정보 요청
        user_info = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    return user_info.json()