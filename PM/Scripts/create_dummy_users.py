import sys
import os

# Backend 폴더를 Python 경로에 추가하여 모듈을 찾을 수 있게 함
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Backend'))

from database import DB_session
from models.user import UserInfo, UserRole
from core.security import get_password_hash
import uuid

def create_dummy_users():
    db = DB_session()
    
    dummy_password_hash = get_password_hash("88888888")
    
    users_to_add = []
    for i in range(1, 6):
        email = f"dummy{i}@moki.com"
        
        # 중복 방지
        existing_user = db.query(UserInfo).filter(UserInfo.email == email).first()
        if existing_user:
            print(f"User {email} already exists. Skipping.")
            continue
            
        user = UserInfo(
            id=uuid.uuid4(),
            email=email,
            password=dummy_password_hash,
            name=f"테스트점주_{i}",
            phone=f"010-8888-000{i}",
            role=UserRole.MANAGER
        )
        users_to_add.append(user)
        
    if users_to_add:
        db.add_all(users_to_add)
        db.commit()
        for u in users_to_add:
            db.refresh(u)
        print(f"Successfully created {len(users_to_add)} dummy users.")
    else:
        print("No dummy users were created.")
        
    db.close()

if __name__ == "__main__":
    create_dummy_users()
