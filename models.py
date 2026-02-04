from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False) # 로그인 시 사용할 ID
    password_hash = Column(String, nullable=False) # 해싱된 비밀번호 저장
    name = Column(String, nullable=False) # 사용자 이름
    role = Column(String, default="user", nullable=False) # 사용자 권한 (admin, user 등)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    login_history = relationship("LoginHistory", back_populates="user")

class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_at = Column(DateTime, default=func.now())
    ip_address = Column(String, nullable=True)
    success = Column(Boolean, default=False)

    user = relationship("User", back_populates="login_history")
