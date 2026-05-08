from database import engine, Base
import models.user
import models.store
from sqlalchemy import text

def drop_and_create():
    print("Dropping all tables...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")

if __name__ == "__main__":
    drop_and_create()
