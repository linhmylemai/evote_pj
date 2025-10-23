from fastapi import APIRouter, HTTPException
from pydantic import BaseModel # <--- ✅ CẦN DÒNG IMPORT NÀY
from sqlmodel import Session, select
from typing import List
import os
from datetime import datetime # <--- ✅ CẦN DÒNG IMPORT NÀY

from server.models.db import Election, Position, Candidate, engine
# ... (các import khác)

# --- Models cho Response ---

# Pydantic model cho thông tin Ứng viên (KHÔNG KẾ THỪA TỪ Candidate)
class CandidateInfo(BaseModel):
    id: int 
    name: str 
    position_name: str

# Pydantic model cho Ballot (KHÔNG KẾ THỪA TỪ Election)
class BallotInfoResponse(BaseModel):
    id: int
    name: str
    start_time: datetime # Dùng datetime vì đây là model phản hồi
    end_time: datetime
    candidates_info: List[CandidateInfo]
    admin_public_key: str
    message: str

router = APIRouter()

# --- Đường dẫn tới Public Key ---
# Giả định đường dẫn Public Key là: Project_eVote/server/keys/admin_public_key.pem
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PUBLIC_KEY_PATH = os.path.join(PROJECT_ROOT, "server", "keys", "admin_public_key.pem")


@router.get("/ballot/{election_id}", response_model=BallotInfoResponse)
def get_ballot_info(election_id: int): # ✅ Thêm tham số ID
    """
    Lấy thông tin về cuộc bầu cử, danh sách ứng viên và Khóa Công khai RSA.
    """
    with Session(engine) as session:
        # 1. Tải thông tin Cuộc bầu cử
        election = session.get(Election, election_id)
        if not election:
            raise HTTPException(status_code=404, detail="Không tìm thấy Cuộc bầu cử với ID này.")
            
        # 2. Tải danh sách Ứng viên/Chức vụ cho cuộc bầu cử
        statement = select(Position, Candidate).join(Candidate).where(
            Position.election_id == election_id
        )
        results = session.exec(statement).all()
        
        candidates_list = []
        for position, candidate in results:
            candidate_info = CandidateInfo(
                id=candidate.id,
                name=candidate.name,
                position_name=position.name
            )
            candidates_list.append(candidate_info)
            
        # 3. Tải Khóa Công khai RSA
        try:
            # Tải chuỗi PEM từ file
            with open(PUBLIC_KEY_PATH, 'r') as f:
                public_key_pem = f.read()
        except FileNotFoundError:
             raise HTTPException(status_code=500, detail="Lỗi server: Không tìm thấy Khóa Công khai của Admin.")

        # 4. Trả về Response
        response_data = BallotInfoResponse(
                id=election.id,
                name=election.name,
                start_time=election.start_time,
                end_time=election.end_time,
                candidates_info=candidates_list,
                admin_public_key=public_key_pem,
                message="Thông tin bầu cử và Khóa Công khai đã sẵn sàng."
            )
        return response_data