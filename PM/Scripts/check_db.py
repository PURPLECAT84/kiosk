from database import DB_session
from models.user import UserInfo, UserRole
from models.kiosk import Kiosk
from sqlalchemy import select

db = DB_session()

print("--- Manager Users & Their Kiosks ---")
stmt = select(UserInfo).where(UserInfo.role == UserRole.MANAGER)
managers = db.scalars(stmt).all()

for m in managers:
    kiosks = db.scalars(select(Kiosk).where(Kiosk.user_id == m.id)).all()
    print(f"{m.email} : {len(kiosks)} kiosks")

