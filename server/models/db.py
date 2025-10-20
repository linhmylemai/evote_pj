from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from typing import Optional, List
from datetime import datetime, date, timezone
import os

# --- Cấu hình Database ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_FILE_NAME = "evote.db"
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)  # ✅ đảm bảo thư mục tồn tại

SQLITE_URL = f"sqlite:///{os.path.join(DATA_DIR, SQLITE_FILE_NAME)}"
engine = create_engine(SQLITE_URL, echo=False)

# --- 1. Master Data ---
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date

# --- MASTER DATA ---

class Candidate(SQLModel, table=True):
    """Ứng viên (Candidate)"""
    __tablename__ = "candidate"
    
    # Mã ứng viên (Primary Key)
    id: Optional[int] = Field(default=None, primary_key=True, title="Mã ứng viên") 
    # Họ và tên
    name: str = Field(index=True, title="Họ và tên")

    # Relationships
    positions: List["Position"] = Relationship(back_populates="candidate")
    decrypted_votes: List["VoteRecordDecrypted"] = Relationship(back_populates="candidate") 


class Voter(SQLModel, table=True):
    """Cử tri (Voter)"""
    __tablename__ = "voter"

    # Mã cử tri (Primary Key)
    id: Optional[int] = Field(default=None, primary_key=True, title="Mã cử tri")
    # CCCD
    cccd: str = Field(index=True, unique=True, title="CCCD")
    # Họ và tên
    name: str = Field(title="Họ và tên")
    # Ngày sinh
    date_of_birth: Optional[date] = Field(default=None, title="Ngày sinh")
    # Email
    email: Optional[str] = Field(default=None, title="Email")
    # SĐT
    phone_number: Optional[str] = Field(default=None, title="SĐT")
    # Địa chỉ
    address: Optional[str] = Field(default=None, title="Địa chỉ")

    # Relationships
    account: Optional["Account"] = Relationship(back_populates="voter")
    decrypted_votes: List["VoteRecordDecrypted"] = Relationship(back_populates="voter")


class Election(SQLModel, table=True):
    """Cuộc bầu (Election)"""
    __tablename__ = "election"

    # Mã cuộc bầu (Primary Key)
    id: Optional[int] = Field(default=None, primary_key=True, title="Mã cuộc bầu")
    # Tiêu đề
    name: str = Field(index=True, title="Tiêu đề")
    # Thời gian bắt đầu
    start_time: datetime = Field(title="Thời gian bắt đầu")
    # Thời gian kết thúc
    end_time: datetime = Field(title="Thời gian kết thúc")

    # Relationships
    encrypted_votes: List["VoteRecordEncrypted"] = Relationship(back_populates="election")
    decrypted_votes: List["VoteRecordDecrypted"] = Relationship(back_populates="election")
    positions_available: List["Position"] = Relationship(back_populates="election")


class Position(SQLModel, table=True):
    """Chức vụ (Position)"""
    __tablename__ = "position"

    # Mã chức vụ (Primary Key)
    id: Optional[int] = Field(default=None, primary_key=True, title="Mã chức vụ")
    # Tên chức vụ
    name: str = Field(index=True, title="Chức vụ")

    # Mã ứng viên (Foreign Key)
    candidate_id: Optional[int] = Field(default=None, foreign_key="candidate.id", title="Mã ứng viên")
    candidate: Optional[Candidate] = Relationship(back_populates="positions")

    # Mã cuộc bầu (Foreign Key)
    election_id: Optional[int] = Field(default=None, foreign_key="election.id", title="Mã cuộc bầu")
    election: Optional[Election] = Relationship(back_populates="positions_available")

# ------------------------------------

class Account(SQLModel, table=True):
    """Tài khoản (Account)"""
    __tablename__ = "account"

    # Tên đăng nhập (Primary Key)
    name_login: str = Field(primary_key=True, index=True, title="Tên đăng nhập")
    # Mật khẩu (Hash)
    password_hash: str = Field(title="Mật khẩu (hash)")
    # Vai trò
    role: str = Field(default="voter", title="Vai trò")

    # Liên kết ID (Mã cử tri) - Dùng mã cử tri để đăng nhập
    voter_id: int = Field(foreign_key="voter.id", index=True, unique=True, title="Mã cử tri liên kết")
    has_voted: bool = Field(default=False, title="Đã bỏ phiếu")
    ballot_token: Optional[str] = Field(default=None, index=True)

    voter: Optional[Voter] = Relationship(back_populates="account")

# ------------------------------------
## TRANSACTIONS & SECURITY RECORDS

class VoteRecordEncrypted(SQLModel, table=True):
    """Bản ghi phiếu bầu đã mã hóa (dữ liệu backend lưu trữ)"""
    __tablename__ = "vote_record_encrypted"

    id: Optional[int] = Field(default=None, primary_key=True, title="Mã bản ghi mã hóa")

    # Dữ liệu mã hóa (từ client)
    enc_key: str = Field(title="Khóa AES đã bọc RSA")
    cipher_vote: str = Field(title="Phiếu đã mã hóa (ciphertext)")
    iv: str = Field(title="IV/Nonce")

    receipt_id: str = Field(index=True, unique=True, title="Mã biên nhận")
    timestamp: datetime = Field(default_factory=datetime.utcnow, title="Thời gian lưu trữ")

    # Mã cuộc bầu (FK)
    election_id: int = Field(foreign_key="election.id", index=True, title="Mã cuộc bầu")
    election: Optional[Election] = Relationship(back_populates="encrypted_votes")
    
    # Relationship to decrypted record (1:1)
    decrypted_record: Optional["VoteRecordDecrypted"] = Relationship(back_populates="encrypted_record")


class VoteRecordDecrypted(SQLModel, table=True):
    """Phiếu bầu (Phiếu đã giải mã - Dùng để kiểm phiếu)"""
    __tablename__ = "vote_record_decrypted"

    # Mã phiếu (Primary Key)
    id: Optional[int] = Field(default=None, primary_key=True, title="Mã phiếu")

    # Mã cuộc bầu (FK)
    election_id: int = Field(foreign_key="election.id", index=True, title="Mã cuộc bầu")
    election: Optional[Election] = Relationship(back_populates="decrypted_votes")
    
    # Mã cử tri (FK)
    voter_id: int = Field(foreign_key="voter.id", index=True, title="Mã cử tri")
    voter: Optional[Voter] = Relationship(back_populates="decrypted_votes")
    
    # Mã ứng viên (FK)
    candidate_id: int = Field(foreign_key="candidate.id", index=True, title="Mã ứng viên được chọn")
    candidate: Optional[Candidate] = Relationship(back_populates="decrypted_votes")

    # Thời gian bỏ phiếu
    timestamp: datetime = Field(title="Thời gian bỏ phiếu")
    # Hợp lệ
    is_valid: bool = Field(default=True, title="Hợp lệ") 
    
    # Liên kết đến bản ghi mã hóa ban đầu (1:1)
    encrypted_record_id: Optional[int] = Field(foreign_key="vote_record_encrypted.id", unique=True, title="Mã bản ghi mã hóa gốc")
    encrypted_record: Optional[VoteRecordEncrypted] = Relationship(back_populates="decrypted_record")


# --- 3. Khởi tạo ---

def create_db_and_tables():
    """Tạo database file và các bảng nếu chưa tồn tại."""
    print(f"Đang tạo database tại: {SQLITE_URL.split('///')[1]}")
    SQLModel.metadata.create_all(engine)
    print("✅ Tạo database và các bảng thành công.")

def get_session():
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    create_db_and_tables()
