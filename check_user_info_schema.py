import sys
import os
from sqlalchemy import inspect
from database import engine

inspector = inspect(engine)
columns = inspector.get_columns('user_info')
for col in columns:
    print(f"{col['name']}: nullable={col['nullable']}")
