# server/services/tokens.py

from sqlmodel import Session, select
import uuid
import secrets
from typing import Optional
from server.models.db import Account, engine

# LƯU Ý: Dùng secrets.token_urlsafe(16) để sinh token ngẫu nhiên
TOKEN_LENGTH = 32 # Chiều dài của Ballot Token

def generate_ballot_token(voter_id: int) -> Optional[str]:
    """Sinh và lưu Ballot Token cho Cử tri hợp lệ."""
    token = secrets.token_urlsafe(TOKEN_LENGTH) # Sinh token ngẫu nhiên
    
    with Session(engine) as session:
        # Tìm account liên kết với voter_id
        statement = select(Account).where(Account.voter_id == voter_id)
        account = session.exec(statement).first()
        
        if account:
            # Gán token mới
            account.ballot_token = token
            session.add(account)
            session.commit()
            session.refresh(account)
            return token
            
    return None

def check_and_use_ballot_token(token: str) -> Optional[int]:
    """Kiểm tra tính hợp lệ của token và đánh dấu cử tri đã bỏ phiếu."""
    with Session(engine) as session:
        # Tìm account bằng token và đảm bảo chưa bỏ phiếu
        statement = select(Account).where(
            Account.ballot_token == token,
            Account.has_voted == False
        )
        account = session.exec(statement).first()

        if account:
            # ✅ Token hợp lệ và chưa dùng. Đánh dấu đã dùng VÀ xóa token (tùy chọn)
            account.has_voted = True
            account.ballot_token = None # Xóa token sau khi dùng
            session.add(account)
            session.commit()
            return account.voter_id
            
    return None # Token không hợp lệ hoặc đã được sử dụng