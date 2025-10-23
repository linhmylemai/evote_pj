# server/routes/login.py (Đã sửa lỗi logic HASHING)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional

# KHÔNG CẦN import hash_password nữa
from server.models.db import Account, Voter, engine
from server.services.tokens import generate_ballot_token
# ✅ Import check_password
from common.crypto import check_password 

router = APIRouter()

class LoginRequest(BaseModel):
    name_login: str
    password: str

class LoginResponse(BaseModel):
    voter_name: str
    ballot_token: str
    message: str


@router.post("/login", response_model=LoginResponse)
def login_user(user_credentials: LoginRequest):
    """
    Endpoint xác thực người dùng. Nếu thành công, sinh Ballot Token.
    """
    
    with Session(engine) as session:
        # 1. Tìm tài khoản bằng Tên đăng nhập
        statement = select(Account).where(
            Account.name_login == user_credentials.name_login
        )
        account = session.exec(statement).first()

        if not account:
            # Sửa thông báo để tránh leak thông tin: chỉ báo lỗi chung
            raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc Mật khẩu không chính xác.")
        
        # 2. ✅ SO SÁNH MẬT KHẨU BẰNG HÀM check_password (CÁCH CHÍNH XÁC)
        # account.password_hash là string, cần chuyển về bytes để bcrypt làm việc
        stored_hash_bytes = account.password_hash.encode('utf-8')
        
        if not check_password(user_credentials.password, stored_hash_bytes):
            raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc Mật khẩu không chính xác.")
        
        if account.has_voted:
            raise HTTPException(status_code=403, detail="Cử tri này đã bỏ phiếu.")

        # 3. Xác thực thành công -> Sinh Ballot Token
        ballot_token = generate_ballot_token(account.voter_id)
        
        # 4. Lấy tên cử tri để trả về
        voter = session.get(Voter, account.voter_id)
        voter_name = voter.name if voter else "Không rõ tên"
        
        return LoginResponse(
            voter_name=voter_name,
            ballot_token=ballot_token,
            message="Đăng nhập thành công. Đã nhận mã thông hành (Ballot Token)."
        )