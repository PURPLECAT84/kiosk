import asyncio
from playwright.async_api import async_playwright
import time
import uuid

async def run_qa_test(num_users=100):
    print(f"[QA START] Testing {num_users} dummy signups.")
    success_count = 0
    fail_count = 0

    async with async_playwright() as p:
        # 헤드리스 모드(화면 안보임)로 실행 시 더 빠르지만, 유저가 애니데스크로 보길 원하므로 띄워줍니다.
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context()
        page = await context.new_page()

        for i in range(1, num_users + 1):
            dummy_email = f"testuser_{i}_{uuid.uuid4().hex[:6]}@moki.com"
            dummy_pw = "Password123!"
            dummy_name = f"테스트점주_{i}"
            dummy_phone = f"010-{i:04d}-5678"

            print(f"[{i}/{num_users}] 가입 시도: {dummy_email} ...", end=" ")

            try:
                # 0. 로그인 페이지 진입
                await page.goto("http://localhost:5173/login")
                await page.wait_for_selector('text=계정이 없으신가요?')
                
                # 1. 회원가입 링크 클릭하여 이동
                await page.click('text=회원가입')
                await page.wait_for_url("**/signup", timeout=5000)
                await page.wait_for_selector('input[type="email"]')

                # 2. 정보 입력
                await page.fill('input[type="email"]', dummy_email)
                await page.fill('input[type="password"]', dummy_pw)
                await page.fill('input[type="text"][placeholder="홍길동"]', dummy_name)
                await page.fill('input[type="text"][placeholder="010-0000-0000"]', dummy_phone)

                # 3. 제출
                await page.click('button[type="submit"]')

                # 4. 로그인 페이지로 넘어갔는지 확인 (성공 시 /login 으로 라우팅 됨)
                await page.wait_for_url("**/login", timeout=10000)
                
                # 5. 로그인 테스트
                await page.fill('input[type="email"]', dummy_email)
                await page.fill('input[type="password"]', dummy_pw)
                await page.click('button[type="submit"]')
                
                # 6. 대시보드로 넘어갔는지 확인
                await page.wait_for_url("**/", timeout=10000)
                
                # 7. 로그아웃
                await page.click('text=로그아웃')
                await page.wait_for_url("**/login", timeout=5000)

                print("[SUCCESS] 가입 -> 로그인 -> 로그아웃 완료")
                success_count += 1
            except Exception as e:
                print(f"[FAIL] 원인: {e}")
                fail_count += 1
                # 스크린샷 캡처
                await page.screenshot(path=f"qa_error_{i}.png")
                # 테스트 환경 복구를 위해 다시 signup으로 이동
                await page.goto("http://localhost:5173/signup")

        print("========================================")
        print(f"[QA COMPLETE] Total: {num_users} | Success: {success_count} | Fail: {fail_count}")
        print("========================================")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_qa_test(100))
