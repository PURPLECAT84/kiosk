from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models import Store, User, Shelve
from schemas import ShelveCreate, ShelveResponse, ShelveUpdate
from routers.users import get_current_user
from typing import List
import uuid

router = APIRouter(prefix = "/shelves", tags = ["shelves"])

@router.post("/store/{store_id}/shelve", response_model = ShelveResponse, status_code = status. HTTP_201_CREATED, summary = "매대 생성", description = "신규 매대 생성")
async def create_shelve(
    store_id : uuid.UUID,
    shelve : ShelveCreate, 
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)):
    
    store_stmt= select(Store).where(Store.id == store_id)
    target_store = db.execute(store_stmt).scalars().first()
    if not target_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "해당 매장을 찾을 수 없습니다")
    
    if current_user.authority not in ["master","dev"] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "본인 매장에만 매대를 생성할 수 있습니다")

    stmt = select(Shelve).where(Shelve.name == shelve.name, Shelve.store_id == store_id)
    exsisting_shelve = db.execute(stmt).scalars().first()

    if exsisting_shelve:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail = "이미 존재하는 매대입니다")

    db_shelve = Shelve(
        name = shelve.name,
        terminal_id = shelve.terminal_id,
        business_number = shelve.business_number,
        vender_code = shelve.vender_code,
        store_id = target_store.id)

    db.add(db_shelve)
    db.commit()
    db.refresh(db_shelve)

    return db_shelve

@router.get("/store/{store_id}/shelve", response_model = List[ShelveResponse], summary = "매대 조회", description = "매장 내 매대 리스트 조회")
async def read_shelve(
    store_id : uuid.UUID, 
    current_user: User = Depends(get_current_user), 
    db : Session = Depends(get_db)):
    
    store_stmt= select(Store).where(Store.id == store_id)
    target_store = db.execute(store_stmt).scalars().first()
    if not target_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "해당 매장을 찾을 수 없습니다")
    
    if current_user.authority not in ["master","dev"] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "본인 매장에만 매대를 조회할 수 있습니다")

    shelve_stmt = select(Shelve).where(Shelve.store_id == store_id)
    shelves = db.execute(shelve_stmt).scalars().all()

    return shelves

@router.patch("/store/{store_id}/shelve/{shelve_id}", response_model = ShelveResponse, summary = "매대 수정", description = "매대 정보 수정")
async def update_shelve(
    store_id : uuid.UUID, 
    shelve_id : uuid.UUID,
    shelve : ShelveUpdate, 
    current_user: User = Depends(get_current_user), 
    db : Session = Depends(get_db)):
    
    store_stmt= select(Store).where(Store.id == store_id)
    target_store = db.execute(store_stmt).scalars().first()
    if not target_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "해당 매장을 찾을 수 없습니다")
    
    if current_user.authority not in ["master","dev"] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "본인 매장에만 매대를 수정할 수 있습니다")

    shelve_stmt = select(Shelve).where(Shelve.id == shelve_id, Shelve.store_id == store_id)
    target_shelve = db.execute(shelve_stmt).scalars().first()

    if not target_shelve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "해당 매대를 찾을 수 없습니다")

    if shelve.name is not None:
        target_shelve.name = shelve.name
    if shelve.terminal_id is not None:
        target_shelve.terminal_id = shelve.terminal_id
    if shelve.business_number is not None:
        target_shelve.business_number = shelve.business_number
    if shelve.vender_code is not None:
        target_shelve.vender_code = shelve.vender_code

    db.add(target_shelve)
    db.commit()
    db.refresh(target_shelve)

    return target_shelve

@router.delete("/store/{store_id}/shelve/{shelve_id}", status_code = status.HTTP_204_NO_CONTENT, summary = "매대 삭제", description = "매대 삭제")
async def delete_shelve(
    store_id : uuid.UUID, 
    shelve_id : uuid.UUID,
    current_user: User = Depends(get_current_user), 
    db : Session = Depends(get_db)):
    
    store_stmt= select(Store).where(Store.id == store_id)
    target_store = db.execute(store_stmt).scalars().first()
    if not target_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "해당 매장을 찾을 수 없습니다")
    
    if current_user.authority not in ["master","dev"] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "본인 매장에만 매대를 삭제할 수 있습니다")

    shelve_stmt = select(Shelve).where(Shelve.id == shelve_id, Shelve.store_id == store_id)
    target_shelve = db.execute(shelve_stmt).scalars().first()

    if not target_shelve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "해당 매대를 찾을 수 없습니다")

    db.delete(target_shelve)
    db.commit()

    return None