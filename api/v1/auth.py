from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserLogin, Token, UserResponse, LoginHistoryCreate, UserCreate # Added UserCreate
from crud import user as crud_user
from auth_utils import verify_password, create_access_token
from models import User

router = APIRouter()

@router.post("/login", response_model=Token, summary="사용자 로그인")
async def login_for_access_token(request: Request, user_login: UserLogin, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_user_id(db, user_login.user_id)
    ip_address = request.client.host if request.client else None
    login_success = False

    if not db_user or not verify_password(user_login.password, db_user.password_hash):
        # 로그인 실패 시에도 이력 저장 (사용자가 없는 경우 user_id는 임시로 None으로 처리)
        temp_user_id = db_user.id if db_user else None # Ensure we only use db_user.id if db_user exists
        crud_user.create_login_history(db, LoginHistoryCreate(user_id=temp_user_id, success=False), ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 로그인 성공
    login_success = True
    crud_user.create_login_history(db, LoginHistoryCreate(user_id=db_user.id, success=True), ip_address)

    access_token = create_access_token(data={"sub": db_user.user_id, "role": db_user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# 개발/테스트용 사용자 생성 엔드포인트 (실제 운영에서는 권한 관리 필요)
@router.post("/register", response_model=UserResponse, summary="새 사용자 등록 (개발용)", status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_user_id(db, user_create.user_id)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID already registered")
    return crud_user.create_user(db=db, user=user_create)