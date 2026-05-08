from database import DB_session
import sys
from models.user import User
from models.store import Store
from sqlalchemy import select

db = DB_session()

stmt = select(User).where(User.authority == 'manager')
managers = db.scalars(stmt).all()

for m in managers:
    stores = db.scalars(select(Store).where(Store.user_id == m.id)).all()
    if stores:
        print(f"FOUND MANAGER WITH STORE: {m.email} / stores: {len(stores)}")
        sys.exit(0)
print("NO MANAGER WITH STORE FOUND")
