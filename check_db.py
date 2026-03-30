from database import DB_session
from models.user import User
from models.store import Store
from sqlalchemy import select

db = DB_session()

print("--- Manager Users & Their Stores ---")
stmt = select(User).where(User.authority == 'manager')
managers = db.scalars(stmt).all()

for m in managers:
    stores = db.scalars(select(Store).where(Store.user_id == m.id)).all()
    print(f"{m.email} : {len(stores)} stores")
