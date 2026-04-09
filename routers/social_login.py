import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from supabase import create_client, Client

# 환경 변수를 명시적으로 한 번 더 로드하여 안정성을 높입니다.
load_dotenv()

"""======================================================
🔑 간편 로그인 (소셜 로그인) 세팅
======================================================"""
# Supabase 환경 변수를 불러오고 클라이언트를 생성합니다.
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") # 주의: 절대 외부에 노출되면 안 되는 보안 키 (또는 anon 키)

if not SUPABASE_URL or not SUPABASE_KEY:
    # 환경 변수가 없으면 서버 구동 시 즉시 에러를 발생시켜 문제를 알도록 합니다.
    raise RuntimeError("Supabase 환경변수(URL, KEY)가 설정되지 않았습니다. .env 파일을 확인해주세요.")

# Supabase 클라이언트를 초기화 (연결) 합니다.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 소셜 로그인 전용 라우터를 생성합니다.
auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication (소셜 로그인)"]
)

@auth_router.get("/{provider}/login", summary="카카오/구글 소셜 로그인 창으로 이동")
async def social_login(provider: str):
    """
    지원 플랫폼: 'kakao', 'google'
    이 API 주소로 접속하면, 해당 소셜 플랫폼(카카오/구글)의 로그인 창으로 자동 이동(리다이렉트) 시킵니다.
    """
    # 1. 올바른 소셜 로그인 플랫폼을 요청했는지 검사합니다.
    allowed_providers = ["kakao", "google"]
    if provider not in allowed_providers:
        raise HTTPException(status_code=400, detail="현재 지원하지 않는 소셜 로그인 수단입니다.")

    try:
        # 2. Supabase에 로그인 창 주소(URL)를 요청합니다.
        # redirect_to: 로그인을 성공的に 마친 뒤 돌아올 '프론트엔드(화면)' 주소입니다.
        # (현재는 따로 프론트엔드 화면이 없거나 개발 단계이므로 localhost:3000로 설정합니다)
        res = supabase.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": "http://localhost:3000/auth/callback" 
            }
        })

        # 3. 발급받은 로그인 URL로 사용자의 화면을 강제로 이동시킵니다!
        return RedirectResponse(url=res.url)

    except Exception as e:
        # 에러가 발생하면 어떤 문제인지 알려줍니다.
        raise HTTPException(status_code=500, detail=f"소셜 로그인 연동 중 오류가 발생했습니다: {str(e)}")