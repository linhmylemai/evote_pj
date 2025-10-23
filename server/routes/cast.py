# server/routes/cast.py (Phiên bản đã sửa lỗi và tối ưu)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
import uuid
from datetime import datetime

from server.models.db import Account, VoteRecordEncrypted, engine 
from server.services.tokens import check_and_use_ballot_token # ✅ Đã sửa import

router = APIRouter()

class CastRequest(BaseModel):
    ballot_token: str
    enc_key: str        
    cipher_vote: str    
    iv: str             

class CastResponse(BaseModel):
    receipt_id: str
    message: str


@router.post("/cast", response_model=CastResponse)
def cast_vote(cast_data: CastRequest):
    """
    Xác thực token, đánh dấu cử tri đã bỏ phiếu và lưu phiếu bầu mã hóa.
    """
    ELECTION_ID = 1 # Giả định Mã Cuộc bầu là 1
    
    # 1. Xác thực Token, kiểm tra trạng thái, ĐÁNH DẤU ĐÃ BỎ PHIẾU, và TIÊU HỦY TOKEN
    # Hàm này trả về voter_id nếu hợp lệ VÀ đã cập nhật trạng thái DB thành has_voted=True
    voter_id = check_and_use_ballot_token(cast_data.ballot_token)

    if voter_id is None:
        # Nếu token không hợp lệ, đã dùng, hoặc cử tri đã bỏ phiếu
        raise HTTPException(status_code=401, detail="Ballot Token không hợp lệ, đã được sử dụng, hoặc cử tri đã bỏ phiếu.")

    with Session(engine) as session:
        # 2. Lấy dữ liệu mã hóa (Dạng chuỗi Base64)
        enc_key_str = cast_data.enc_key
        cipher_vote_str = cast_data.cipher_vote
        iv_str = cast_data.iv

        # 3. Sinh Receipt ID và Lưu bản ghi phiếu bầu
        receipt_id = str(uuid.uuid4())
        
        new_vote_record = VoteRecordEncrypted(
            receipt_id=receipt_id,
            enc_key=enc_key_str,
            cipher_vote=cipher_vote_str,
            iv=iv_str,
            election_id=ELECTION_ID,
            # Lưu voter_id vào bản ghi mã hóa để dễ dàng đối chiếu
            # (Giả định bạn muốn thêm voter_id vào VoteRecordEncrypted)
            # Nếu không có cột voter_id trong VoteRecordEncrypted, hãy bỏ dòng này.
            # voter_id=voter_id, 
        )
        session.add(new_vote_record)
        session.commit()
        
    # 4. Trả về Biên nhận
    return CastResponse(
        receipt_id=receipt_id,
        message="Phiếu bầu đã được lưu trữ thành công và mã biên nhận đã được cấp."
    )