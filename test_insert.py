import uuid
from sqlalchemy.orm import Session
from database import engine
from models.user import UserInfo, UserRole, UserStatus

def test_insert_user():
    db = Session(engine)
    try:
        new_id = uuid.uuid4()
        new_user = UserInfo(
            id=new_id,
            email="test_social@test.com",
            name="Test User",
            phone="010-0000-0000",
            role=UserRole.STAFF,
            status=UserStatus.PENDING
        )
        db.add(new_user)
        db.commit()
        print("SUCCESS! Inserted user successfully.")
        db.delete(new_user)
        db.commit()
    except Exception as e:
        print("ERROR:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_insert_user()
