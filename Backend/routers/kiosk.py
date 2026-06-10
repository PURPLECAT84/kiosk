from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models.kiosk import Kiosk
from models.user import UserInfo, UserRole
from schemas.kiosk import KioskCreate, KioskResponse, KioskUpdate, KioskAdminResponse, KioskAdminCreate, KioskAdminUpdate
from core.dependency import require_roles, get_current_user
from typing import List
import uuid
import random
import string

router = APIRouter()

# 일반적인 키오스크 권한: DEV, HEAD, MASTER, MANAGER
general_roles = [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]
# 결제 정보 수정 권한: DEV, HEAD
billing_roles = [UserRole.DEV, UserRole.HEAD]

def generate_kiosk_code(db: Session) -> str:
    """KS + 6자리 알파벳 대문자 및 숫자 조합의 고유코드 생성"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "KS" + "".join(random.choice(chars) for _ in range(6))
        # 중복 체크
        stmt = select(Kiosk).where(Kiosk.code == code)
        if not db.execute(stmt).scalars().first():
            return code

@router.post("/", response_model=KioskResponse, status_code=status.HTTP_201_CREATED, summary="키오스크 생성")
async def create_kiosk(
    kiosk: KioskCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    # 점주 존재 여부 검증
    owner_stmt = select(UserInfo).where(UserInfo.id == kiosk.user_id)
    owner = db.execute(owner_stmt).scalars().first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="점주(사용자)를 찾을 수 없습니다")
    
    store_name = "미지정 매장"
    if owner.businesses:
        store_name = owner.businesses[0].store_name
        
    code = generate_kiosk_code(db)
    db_kiosk = Kiosk(
        code=code,
        user_id=kiosk.user_id,
        name=kiosk.name,
        model_name=kiosk.model_name,
        type=kiosk.type,
        status=kiosk.status,
        payment_status="NORMAL"
    )
    db.add(db_kiosk)
    db.flush() # UUID 생성을 위해 flush
    
    # 4. KioskAdmin 매핑 (최초 생성 시 점주 및 생성자를 관리자로 매핑)
    from models.kiosk_admin import KioskAdmin
    
    # 4-1. 점주 매핑
    owner_admin = KioskAdmin(
        kiosk_id=db_kiosk.id,
        user_id=owner.id,
        role="MASTER"
    )
    db.add(owner_admin)
    
    # 4-2. 생성자가 점주와 다르고 DEV/HEAD/MASTER 권한인 경우 생성자도 매핑
    if current_user.id != owner.id:
        creator_admin = KioskAdmin(
            kiosk_id=db_kiosk.id,
            user_id=current_user.id,
            role=current_user.role.value
        )
        db.add(creator_admin)
        
    db.commit()
    db.refresh(db_kiosk)
    
    setattr(db_kiosk, "store_name", store_name)
    return db_kiosk


@router.get("/", response_model=List[KioskResponse], summary="키오스크 조회")
async def read_kiosk(
    skip: int = 0,
    limit: int = 100,
    user_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk)
    
    if current_user.role == UserRole.MANAGER:
        stmt = stmt.where(Kiosk.user_id == current_user.id)
    elif user_id:
        stmt = stmt.where(Kiosk.user_id == user_id)
        
    stmt = stmt.offset(skip).limit(limit)
    kiosks = db.execute(stmt).scalars().all()
    
    response_data = []
    for k in kiosks:
        store_name = "미지정 매장"
        if k.owner and k.owner.businesses:
            store_name = k.owner.businesses[0].store_name
        setattr(k, "store_name", store_name)
        response_data.append(k)
        
    return response_data


@router.get("/active-stores", summary="사업자 확인 완료 매장 목록 조회 (키오스크 등록용)")
async def read_active_stores(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    """
    [초보자용 교보재 지침 - 사업자 확인 매장 조회]
    사업자 인증(is_business_verified=True)을 통과한 점주(User)들의 매장 목록만 조회합니다.
    DEV/HEAD 권한인 경우 모든 점주(MANAGER)를 조회할 수 있습니다.
    """
    if current_user.role in [UserRole.DEV, UserRole.HEAD]:
        stmt = select(UserInfo).where(UserInfo.role == UserRole.MANAGER)
    else:
        stmt = select(UserInfo).where(UserInfo.is_business_verified == True)
        if current_user.role == UserRole.MANAGER:
            stmt = stmt.where(UserInfo.id == current_user.id)
        
    users = db.execute(stmt).scalars().all()
    return [{"id": u.id, "name": u.businesses[0].store_name if u.businesses else "미지정 매장", "owner_name": u.name} for u in users]


@router.get("/my", response_model=List[KioskResponse], summary="내가 관리하는 기기 리스트 조회")
async def read_my_kiosks(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    [초보자용 교보재 지침 - 관리 대상 키오스크 조회]
    현재 로그인한 사용자가 관리 권한을 가지고 있는 키오스크 리스트를 반환합니다.
    """
    from models.kiosk_admin import KioskAdmin
    
    if current_user.role in [UserRole.DEV, UserRole.HEAD]:
        stmt = select(Kiosk)
        results = db.execute(stmt).scalars().all()
    else:
        stmt = (
            select(Kiosk)
            .join(KioskAdmin, Kiosk.id == KioskAdmin.kiosk_id)
            .where(KioskAdmin.user_id == current_user.id)
        )
        results = db.execute(stmt).scalars().all()
        
    response_data = []
    for kiosk in results:
        store_name = "미지정 매장"
        if kiosk.owner and kiosk.owner.businesses:
            store_name = kiosk.owner.businesses[0].store_name
        setattr(kiosk, "store_name", store_name)
        response_data.append(kiosk)
        
    return response_data


@router.get("/{kiosk_id}", response_model=KioskResponse, summary="키오스크 상세 조회")
async def get_kiosk_detail(
    kiosk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk).where(Kiosk.id == kiosk_id)
    kiosk = db.execute(stmt).scalars().first()
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다")
    
    # MANAGER 권한 검증: 본인 소유의 키오스크인지 체크
    if current_user.role == UserRole.MANAGER and kiosk.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 소유의 키오스크 정보만 열람할 수 있습니다")
        
    store_name = "미지정 매장"
    if kiosk.owner and kiosk.owner.businesses:
        store_name = kiosk.owner.businesses[0].store_name
        
    setattr(kiosk, "store_name", store_name)
    return kiosk


@router.patch("/{kiosk_id}", response_model=KioskResponse, summary="키오스크 정보 변경")
async def update_kiosk(
    kiosk_id: uuid.UUID,
    body: KioskUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk).where(Kiosk.id == kiosk_id)
    kiosk = db.execute(stmt).scalars().first()
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다")
        
    # MANAGER 권한 검증: 본인 소유의 키오스크인지 체크
    if current_user.role == UserRole.MANAGER and kiosk.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 소유의 키오스크 정보만 수정할 수 있습니다")

    # 결제 정보 수정 권한 제한 검증
    if body.payment_status is not None or body.next_payment_date is not None:
        if current_user.role not in billing_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="결제 정보 변경 권한은 본사(HEAD) 또는 개발자(DEV) 권한만 가능합니다")

    if body.name is not None:
        kiosk.name = body.name
    if body.model_name is not None:
        kiosk.model_name = body.model_name
    if body.status is not None:
        kiosk.status = body.status
    if body.payment_status is not None:
        kiosk.payment_status = body.payment_status
    if body.next_payment_date is not None:
        kiosk.next_payment_date = body.next_payment_date
        
    db.commit()
    db.refresh(kiosk)
    
    store_name = "미지정 매장"
    if kiosk.owner and kiosk.owner.businesses:
        store_name = kiosk.owner.businesses[0].store_name
    
    setattr(kiosk, "store_name", store_name)
    return kiosk


@router.delete("/{kiosk_id}", status_code=status.HTTP_204_NO_CONTENT, summary="키오스크 삭제")
async def delete_kiosk(
    kiosk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk).where(Kiosk.id == kiosk_id)
    kiosk = db.execute(stmt).scalars().first()
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다")
        
    # MANAGER 권한 검증: 본인 소유의 키오스크인지 체크
    if current_user.role == UserRole.MANAGER and kiosk.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 소유의 키오스크만 삭제할 수 있습니다")
        
    db.delete(kiosk)
    db.commit()
    return None


"""===================== 키오스크 관리자 매핑 관리 API ============================"""

@router.get("/{kiosk_id}/admins", response_model=List[KioskAdminResponse], summary="기기별 관리자 리스트 조회")
async def get_kiosk_admins(
    kiosk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    """
    [초보자용 교보재 지침 - 기기별 관리자 조회]
    특정 키오스크(kiosk_id)에 귀속된 관리자(점주, 알바생 등) 목록을 조회합니다.
    - 각 관리자의 이메일, 이름, 연락처 및 기기에 부여된 역할(role)을 함께 반환합니다.
    """
    from models.kiosk_admin import KioskAdmin
    
    # 1. 키오스크 권한 체크 (점주의 경우 자신이 관리자인 기기인지 검증)
    if current_user.role == UserRole.MANAGER:
        stmt_check = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id, KioskAdmin.user_id == current_user.id)
        if not db.execute(stmt_check).scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이 키오스크의 관리자 목록을 볼 권한이 없습니다.")
            
    stmt = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id)
    admins = db.execute(stmt).scalars().all()
    
    response = []
    for admin in admins:
        response.append(KioskAdminResponse(
            user_id=admin.user_id,
            name=admin.user.name,
            email=admin.user.email,
            phone=admin.user.phone,
            role=admin.role,
            created_at=admin.created_at
        ))
    return response


@router.post("/{kiosk_id}/admins", response_model=KioskAdminResponse, summary="기기 관리자 추가")
async def add_kiosk_admin(
    kiosk_id: uuid.UUID,
    body: KioskAdminCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    """
    [초보자용 교보재 지침 - 기기 관리자 추가]
    이메일(email)을 검색하여 존재하는 사용자를 특정 키오스크의 관리자로 등록합니다.
    - 기본적으로 STAFF 권한으로 디폴트 할당하며, 점주는 자신보다 상위 권한의 관리자를 추가할 수 없습니다.
    """
    from models.kiosk_admin import KioskAdmin
    
    # 1. 키오스크 존재 여부 검사
    kiosk_stmt = select(Kiosk).where(Kiosk.id == kiosk_id)
    kiosk = db.execute(kiosk_stmt).scalars().first()
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다.")

    # 2. 현재 요청자의 이 기기에 대한 권한 확인 (DEV/HEAD는 마스터 권한 보유로 간주)
    caller_role = "STAFF"
    if current_user.role in [UserRole.DEV, UserRole.HEAD]:
        caller_role = "DEV"
    else:
        stmt_check = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id, KioskAdmin.user_id == current_user.id)
        admin_rec = db.execute(stmt_check).scalars().first()
        if not admin_rec:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이 키오스크에 관리자를 추가할 권한이 없습니다.")
        caller_role = admin_rec.role

    # STAFF 권한은 다른 관리자를 추가할 수 없음
    if caller_role == "STAFF":
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="STAFF 권한은 관리자를 추가할 수 없습니다.")

    # 3. 추가하려는 유저가 실제로 존재하는지 이메일로 검색
    user_stmt = select(UserInfo).where(UserInfo.email == body.email)
    target_user = db.execute(user_stmt).scalars().first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="입력하신 이메일의 사용자를 찾을 수 없습니다.")

    # 4. 이미 해당 기기의 관리자로 등록되어 있는지 검증
    dup_stmt = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id, KioskAdmin.user_id == target_user.id)
    if db.execute(dup_stmt).scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 이 기기의 관리자로 등록되어 있는 사용자입니다.")

    # 5. 권한 레벨 검증 (본인 권한 이하로만 지정 가능)
    role_levels = {"DEV": 5, "HEAD": 4, "MASTER": 3, "MANAGER": 2, "STAFF": 1}
    caller_level = role_levels.get(caller_role, 1)
    target_level = role_levels.get(body.role, 1)
    
    if target_level > caller_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인보다 높은 권한의 관리자를 임명할 수 없습니다.")

    # 6. KioskAdmin 생성 및 저장
    new_admin = KioskAdmin(
        kiosk_id=kiosk_id,
        user_id=target_user.id,
        role=body.role
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return KioskAdminResponse(
        user_id=new_admin.user_id,
        name=target_user.name,
        email=target_user.email,
        phone=target_user.phone,
        role=new_admin.role,
        created_at=new_admin.created_at
    )


@router.patch("/{kiosk_id}/admins/{user_id}", response_model=KioskAdminResponse, summary="기기 관리자 권한 수정")
async def update_kiosk_admin(
    kiosk_id: uuid.UUID,
    user_id: uuid.UUID,
    body: KioskAdminUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    """
    [초보자용 교보재 지침 - 기기 관리자 권한 수정]
    기존에 귀속된 관리자의 권한 등급을 조정합니다.
    """
    from models.kiosk_admin import KioskAdmin
    
    # 1. 대상 관리자 존재 검증
    target_stmt = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id, KioskAdmin.user_id == user_id)
    target_admin = db.execute(target_stmt).scalars().first()
    if not target_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 관리자 매핑을 찾을 수 없습니다.")

    # 2. 현재 요청자의 권한 확인
    caller_role = "STAFF"
    if current_user.role in [UserRole.DEV, UserRole.HEAD]:
        caller_role = "DEV"
    else:
        stmt_check = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id, KioskAdmin.user_id == current_user.id)
        admin_rec = db.execute(stmt_check).scalars().first()
        if not admin_rec:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이 기기의 권한을 수정할 자격이 없습니다.")
        caller_role = admin_rec.role

    # 3. 권한 수준 검증
    role_levels = {"DEV": 5, "HEAD": 4, "MASTER": 3, "MANAGER": 2, "STAFF": 1}
    caller_level = role_levels.get(caller_role, 1)
    target_level = role_levels.get(body.role, 1)
    
    if target_level > caller_level:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인보다 높은 권한으로 수정할 수 없습니다.")

    # 4. 정보 수정 및 저장
    target_admin.role = body.role
    db.commit()
    db.refresh(target_admin)

    return KioskAdminResponse(
        user_id=target_admin.user_id,
        name=target_admin.user.name,
        email=target_admin.user.email,
        phone=target_admin.user.phone,
        role=target_admin.role,
        created_at=target_admin.created_at
    )


@router.delete("/{kiosk_id}/admins/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="기기 관리자 해제/삭제")
async def delete_kiosk_admin(
    kiosk_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    """
    [초보자용 교보재 지침 - 기기 관리자 해제]
    특정 키오스크의 관리 자격을 박탈하거나 직원 권한을 리스트에서 제외합니다.
    """
    from models.kiosk_admin import KioskAdmin
    
    # 1. 대상 관리자 존재 검증
    target_stmt = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id, KioskAdmin.user_id == user_id)
    target_admin = db.execute(target_stmt).scalars().first()
    if not target_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 관리자 매핑을 찾을 수 없습니다.")

    # 2. 현재 요청자의 권한 확인
    caller_role = "STAFF"
    if current_user.role in [UserRole.DEV, UserRole.HEAD]:
        caller_role = "DEV"
    else:
        stmt_check = select(KioskAdmin).where(KioskAdmin.kiosk_id == kiosk_id, KioskAdmin.user_id == current_user.id)
        admin_rec = db.execute(stmt_check).scalars().first()
        if not admin_rec:
            if current_user.id == user_id:
                pass
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이 기기에서 관리자를 제거할 권한이 없습니다.")
        else:
            caller_role = admin_rec.role

    # 3. 본인 외 타인을 삭제할 때 권한 수준 검증 (본인보다 같거나 높은 레벨을 삭제할 수 없음)
    if current_user.id != user_id:
        role_levels = {"DEV": 5, "HEAD": 4, "MASTER": 3, "MANAGER": 2, "STAFF": 1}
        caller_level = role_levels.get(caller_role, 1)
        target_level = role_levels.get(target_admin.role, 1)
        
        if target_level >= caller_level and caller_role != "DEV":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인과 같거나 더 높은 등급의 관리자는 해제할 수 없습니다.")

    # 4. KioskAdmin 삭제
    db.delete(target_admin)
    db.commit()
    return None
