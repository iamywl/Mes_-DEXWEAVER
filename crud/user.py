from sqlalchemy.orm import Session
from models import User, LoginHistory
from schemas import UserCreate, LoginHistoryCreate
from auth_utils import get_password_hash
from datetime import datetime

def get_user_by_user_id(db: Session, user_id: str):
    return db.query(User).filter(User.user_id == user_id).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(user_id=user.user_id, password_hash=hashed_password, name=user.name, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_login_history(db: Session, login_history: LoginHistoryCreate, ip_address: str = None):
    db_login_history = LoginHistory(
        user_id=login_history.user_id,
        ip_address=ip_address,
        success=login_history.success,
        login_at=datetime.utcnow()
    )
    db.add(db_login_history)
    db.commit()
    db.refresh(db_login_history)
    return db_login_history

# 초기 관리자 사용자 생성 (선택 사항, 개발/테스트용)
def create_initial_admin_user(db: Session):
    if not get_user_by_user_id(db, "admin"):
        admin_user = UserCreate(user_id="admin", password="admin1234", name="Admin User", role="admin")
        create_user(db, admin_user)
        print("Initial admin user 'admin' created with password 'admin1234'")
