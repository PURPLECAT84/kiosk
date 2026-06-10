from database import DB_session
import sys
from models.user import UserInfo, UserRole
from models.kiosk import Kiosk
from sqlalchemy import select

db = DB_session()

stmt = select(UserInfo).where(UserInfo.role == UserRole.MANAGER)
managers = db.scalars(stmt).all()

for m in managers:
    kiosks = db.scalars(select(Kiosk).where(Kiosk.user_id == m.id)).all()
    if kiosks:
        print(f"FOUND MANAGER WITH KIOSK: {m.email} / kiosks: {len(kiosks)}")
        sys.exit(0)
print("NO MANAGER WITH KIOSK FOUND")
