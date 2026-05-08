import asyncio
from sqlalchemy import text
from database import DB_session

def reset_user_table():
    db = DB_session()
    try:
        # PostgreSQL CASCADE 삭제로 user_info 및 연관된 테이블 데이터 모두 삭제
        db.execute(text("TRUNCATE TABLE user_info CASCADE;"))
        db.commit()
        print("[SUCCESS] user_info table has been truncated.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to truncate table: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("--- Supabase User Table Reset ---")
    reset_user_table()
