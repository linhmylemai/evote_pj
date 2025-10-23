# server/routes/login.py (CODE HOÀN CHỈNH)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional

# Import Models và Engine
from server.models.db import Account,Voter, engine 
# Import hàm kiểm tra mật khẩu
from common.crypto import check_password 
# Import hàm sinh token mới
from server.services.tokens import generate_ballot_token #  SỬ DỤNG HÀM CỦA BẠN

router = APIRouter()

# --- 1. Models cho Request và Response ---

class LoginRequest(BaseModel):
    name_login: str
    password: str

class LoginResponse(BaseModel):
    voter_name: str
    ballot_token: str
    message: str

# --- 2. Endpoint Đăng nhập ---
@router.post("/login", response_model=LoginResponse)
def login_for_ballot_token(login_data: LoginRequest):
    """
    Xác thực cử tri và sinh Ballot Token (lưu vào DB)
    """
    
    with Session(engine) as session:
        # 1. Tìm TÀI KHOẢN VÀ CỬ TRI liên kết
        # Join Account và Voter để lấy thông tin trong một truy vấn
        statement = select(Account, Voter).join(Voter).where(
            Account.name_login == login_data.name_login
        )
        result = session.exec(statement).first()

        if not result:
            raise HTTPException(
                status_code=401, 
                detail="Tên đăng nhập hoặc mật khẩu không đúng."
            )
        
        # Lấy ra các đối tượng
        account, voter = result

        # 2. Kiểm tra mật khẩu
        # Dùng `account.password_hash.encode('utf-8')` để chuyển string trong DB thành bytes
        is_correct = check_password(
            login_data.password, 
            account.password_hash.encode('utf-8')
        )
        
        if not is_correct:
            raise HTTPException(
                status_code=401, 
                detail="Tên đăng nhập hoặc mật khẩu không đúng."
            )

        # 3. Kiểm tra trạng thái bỏ phiếu
        if account.has_voted:
             raise HTTPException(
                status_code=403, 
                detail="Cử tri này đã hoàn thành việc bỏ phiếu."
            )

        # 4. Sinh và Lưu Token mới
        # Token vẫn dùng voter_id để liên kết
        token = generate_ballot_token(account.voter_id)

        if not token:
             raise HTTPException(status_code=500, detail="Lỗi server: Không thể tạo token.")
             
        # 5. Trả về tên cử tri (Voter.name)
        return LoginResponse(
            voter_name=voter.name, #  ĐÃ SỬA: Dùng tên từ đối tượng Voter
            ballot_token=token,
            message="Đăng nhập thành công. Token đã sẵn sàng để bỏ phiếu."
        )