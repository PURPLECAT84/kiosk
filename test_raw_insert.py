import uuid
from sqlalchemy import text
from database import engine

def test_raw_sql_insert():
    with engine.connect() as conn:
        try:
            new_id = str(uuid.uuid4())
            rs = conn.execute(text("""
                INSERT INTO public.user_info (id, email, name, role, status, phone)
                VALUES (
                    :id,
                    'rawsql_test@test.com',
                    'Raw Sql',
                    'STAFF',
                    'PENDING',
                    '010-0000-0000'
                )
            """), {"id": new_id})
            conn.commit()
            print("RAW SQL SUCCESS")
            conn.execute(text("DELETE FROM public.user_info WHERE id = :id"), {"id": new_id})
            conn.commit()
        except Exception as e:
            print("RAW SQL ERROR:", e)

if __name__ == "__main__":
    test_raw_sql_insert()
