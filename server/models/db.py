# server/models/db.py
from sqlmodel import SQLModel, Field, Session, create_engine, Relationship
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# ===== ABSOLUTE DB PATH (không bị lệch khi chạy từ evote_tk) =====
DB_PATH = (Path(__file__).resolve().parents[1] / "data" / "evote.db")  # .../server/data/evote.db
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

class Election(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    votes: List["VoteRecordEncrypted"] = Relationship(back_populates="election")

class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    position: Optional[str] = None

class Voter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    role: Optional[str] = "user"

class VoteRecordEncrypted(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    election_id: int = Field(foreign_key="election.id")
    voter_id: int = Field(foreign_key="voter.id")
    enc_key: str
    iv: str
    cipher_vote: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    election: Optional[Election] = Relationship(back_populates="votes")
    decrypted_record: Optional["VoteRecordDecrypted"] = Relationship(back_populates="encrypted_record")

class VoteRecordDecrypted(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    election_id: int
    voter_id: int
    candidate_id: int
    timestamp: datetime
    is_valid: bool = True
    encrypted_record_id: int = Field(foreign_key="voterecordencrypted.id")

    encrypted_record: Optional[VoteRecordEncrypted] = Relationship(back_populates="decrypted_record")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    print("✅ Database initialized:", DB_PATH)

if __name__ == "__main__":
    init_db()
