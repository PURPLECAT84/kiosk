import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()
DB_URL = os.getenv("DB_URL")

print("Connecting to DB:", DB_URL)
engine = create_engine(DB_URL)

with engine.connect() as conn:
    # 1. user_info 테이블에 is_business_verified 컬럼 추가
    try:
        conn.execute(text("ALTER TABLE user_info ADD COLUMN is_business_verified BOOLEAN DEFAULT FALSE;"))
        conn.commit()
        print("Added 'is_business_verified' column to 'user_info' table.")
    except Exception as e:
        conn.rollback()
        if "already exists" in str(e):
            print("'is_business_verified' column already exists in 'user_info'.")
        else:
            print("Error adding 'is_business_verified':", e)

    # 2. business_info 테이블에 business_name 컬럼 추가
    try:
        conn.execute(text("ALTER TABLE business_info ADD COLUMN business_name VARCHAR(100);"))
        conn.commit()
        print("Added 'business_name' column to 'business_info' table.")
    except Exception as e:
        conn.rollback()
        if "already exists" in str(e):
            print("'business_name' column already exists in 'business_info'.")
        else:
            print("Error adding 'business_name':", e)

    # 3. business_info 테이블에 store_name 컬럼 추가
    try:
        conn.execute(text("ALTER TABLE business_info ADD COLUMN store_name VARCHAR(100);"))
        conn.commit()
        print("Added 'store_name' column to 'business_info' table.")
    except Exception as e:
        conn.rollback()
        if "already exists" in str(e):
            print("'store_name' column already exists in 'business_info'.")
        else:
            print("Error adding 'store_name':", e)

    # 4. business_info 테이블의 representative_phone 컬럼을 NULL 허용으로 완화
    try:
        conn.execute(text("ALTER TABLE business_info ALTER COLUMN representative_phone DROP NOT NULL;"))
        conn.commit()
        print("Set 'representative_phone' column to nullable in 'business_info' table.")
    except Exception as e:
        conn.rollback()
        print("Error altering 'representative_phone':", e)

    # 5. kiosk_admins 테이블 생성 (존재하지 않을 경우)
    try:
        create_kiosk_admins_sql = """
        CREATE TABLE IF NOT EXISTS kiosk_admins (
            id UUID PRIMARY KEY,
            kiosk_id UUID NOT NULL REFERENCES kiosks(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES user_info(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        conn.execute(text(create_kiosk_admins_sql))
        conn.commit()
        print("'kiosk_admins' table created or already exists.")
    except Exception as e:
        conn.rollback()
        print("Error creating 'kiosk_admins' table:", e)

    # 6. order_info 테이블에 kiosk_id 컬럼 추가
    try:
        conn.execute(text("ALTER TABLE order_info ADD COLUMN kiosk_id UUID REFERENCES kiosks(id) ON DELETE SET NULL;"))
        conn.commit()
        print("Added 'kiosk_id' column to 'order_info' table.")
    except Exception as e:
        conn.rollback()
        if "already exists" in str(e):
            print("'kiosk_id' column already exists in 'order_info'.")
        else:
            print("Error adding 'kiosk_id':", e)

print("DB patching complete.")
