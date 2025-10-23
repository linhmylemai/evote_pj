  # ✅ Script CLI:
 #  - Đọc danh sách phiếu từ server/data/evote.db
  #  - Dùng RSA-OAEP (private key) để giải mã AES key
  #  - Dùng AES-GCM để giải mã lá phiếu
 #  - Đếm và in kết quả bầu cử

# admin/tally.py (Đã sửa lỗi Import và Logic Giải mã)

import sys
import os
from sqlmodel import Session, select
from datetime import datetime
import base64
import json
from typing import Optional, List, Dict

# Thiết lập Python Path để import common/crypto và server/models/db
# Đường dẫn từ admin/ -> Project_eVote/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# ✅ Cập nhật imports để khớp với hàm mới
from common.crypto import load_private_key, rsa_decrypt, aes_gcm_decrypt
from server.models.db import (
    engine, 
    Election, 
    VoteRecordEncrypted, 
    VoteRecordDecrypted, 
    Candidate, 
    Voter
)

# Đường dẫn đến Private Key
PRIVATE_KEY_PATH = os.path.join(PROJECT_ROOT, "admin", "keys", "admin_private_key.pem")

# --------------------------
# KHỐI CODE KIỂM TRA ĐƯỜNG DẪN
# --------------------------
def check_key_path():
    print("------------------------------------------")
    print(f"Đang kiểm tra đường dẫn Private Key:")
    print(f"Đường dẫn tuyệt đối dự kiến: {os.path.abspath(PRIVATE_KEY_PATH)}")
    
    if os.path.exists(PRIVATE_KEY_PATH):
        print("✅ TÌM THẤY! Đường dẫn Private Key đã chính xác.")
        return True
    else:
        print("❌ KHÔNG TÌM THẤY! Vui lòng kiểm tra các mục sau:")
        print(f"1. Đảm bảo thư mục 'admin/keys/' đã tồn tại.")
        print(f"2. Đảm bảo bạn đã chạy file 'generate_keys.py' để sinh file 'admin_private_key.pem'.")
        print(f"3. Đảm bảo bạn chạy 'python admin/tally.py' từ thư mục GỐC của dự án (Project_eVote).")
        return False

# Chạy kiểm tra trước khi bắt đầu kiểm phiếu
if not check_key_path():
    # Dừng script nếu không tìm thấy khóa
    sys.exit(1)
# --- Hàm Chính: Kiểm phiếu ---

def tally_votes(election_id: int):
    """
    Tải Private Key, giải mã tất cả phiếu bầu mã hóa và lưu vào bảng giải mã.
    """
    print("====================================")
    print(f"🗳️ BẮT ĐẦU KIỂM PHIẾU CHO CUỘC BẦU CỬ ID: {election_id}")
    print("====================================")

    # 1. Tải Private Key
    try:
        private_key = load_private_key(PRIVATE_KEY_PATH)
        print("✅ Tải Private Key thành công.")
    except Exception as e:
        print(f"❌ LỖI: Không thể tải Private Key từ {PRIVATE_KEY_PATH}. Vui lòng kiểm tra lại đường dẫn và file.")
        print(f"Chi tiết: {e}")
        return

    total_encrypted_votes = 0
    total_decrypted_success = 0
    tally_results: Dict[str, int] = {}
    
    with Session(engine) as session:
        # Kiểm tra Cuộc bầu cử
        election = session.get(Election, election_id)
        if not election:
            print(f"❌ LỖI: Không tìm thấy Cuộc bầu cử với ID={election_id}.")
            return

        # 2. Tải tất cả phiếu bầu mã hóa
        statement = select(VoteRecordEncrypted).where(
            VoteRecordEncrypted.election_id == election_id
        )
        encrypted_votes: List[VoteRecordEncrypted] = session.exec(statement).all()
        total_encrypted_votes = len(encrypted_votes)
        
        print(f"Đã tìm thấy {total_encrypted_votes} phiếu bầu mã hóa.")

        # 3. Tiến hành giải mã từng phiếu
        for record in encrypted_votes:
            # Bỏ qua nếu phiếu này đã được giải mã trước đó
            if record.decrypted_record:
                print(f"   -> Phiếu {record.id}: Đã giải mã. Bỏ qua.")
                continue

            try:
                # 3a. Giải mã Khóa AES (session key) bằng RSA Private Key
                enc_key_bytes = base64.b64decode(record.enc_key.encode('utf-8'))
                # ✅ Dùng hàm rsa_decrypt mới của bạn
                aes_key = rsa_decrypt(private_key, enc_key_bytes)

                if aes_key is None:
                    raise Exception("Giải mã Khóa AES thất bại.")

                # 3b. Giải mã Phiếu bầu bằng AES-GCM
                cipher_vote_bytes = base64.b64decode(record.cipher_vote.encode('utf-8'))
                iv_bytes = base64.b64decode(record.iv.encode('utf-8'))
                
                # ✅ Dùng hàm aes_gcm_decrypt mới của bạn
                decrypted_bytes = aes_gcm_decrypt(aes_key, iv_bytes, cipher_vote_bytes)
                decrypted_json_str = decrypted_bytes.decode('utf-8')

                # 3c. Phân tích nội dung phiếu bầu
                # Giả định: Phiếu bầu có định dạng {"candidate_id": X, "voter_id": Y}
                decrypted_data = json.loads(decrypted_json_str)
                selected_candidate_id = decrypted_data.get("candidate_id")
                voter_id_from_vote = decrypted_data.get("voter_id") 

                if not selected_candidate_id or not voter_id_from_vote:
                    raise Exception("Nội dung phiếu bầu không đúng định dạng.")

                # 4. Lưu kết quả vào bảng giải mã
                decrypted_record = VoteRecordDecrypted(
                    election_id=record.election_id,
                    voter_id=voter_id_from_vote,
                    candidate_id=selected_candidate_id,
                    timestamp=record.timestamp,
                    is_valid=True,
                    encrypted_record_id=record.id
                )
                session.add(decrypted_record)
                
                # Cập nhật tổng kết quả
                candidate_name = session.get(Candidate, selected_candidate_id).name if session.get(Candidate, selected_candidate_id) else f"ID {selected_candidate_id}"
                tally_results[candidate_name] = tally_results.get(candidate_name, 0) + 1
                total_decrypted_success += 1
                
            except Exception as e:
                print(f"   -> Phiếu {record.id} LỖI GIẢI MÃ: {e}. Đánh dấu KHÔNG HỢP LỆ.")
                
        session.commit()
        
    # 5. In kết quả cuối cùng
    print("\n====================================")
    print("✨ KẾT QUẢ KIỂM PHIẾU CUỐI CÙNG ✨")
    print("====================================")
    print(f"Tổng số phiếu mã hóa: {total_encrypted_votes}")
    print(f"Số phiếu giải mã thành công: {total_decrypted_success}")
    print(f"Số phiếu không giải mã được: {total_encrypted_votes - total_decrypted_success}")
    print("\n--- KẾT QUẢ BỎ PHIẾU ---")
    
    sorted_results = sorted(tally_results.items(), key=lambda item: item[1], reverse=True)
    
    for candidate, count in sorted_results:
        print(f"{candidate:25}: {count} phiếu")
        
    print("====================================")
    print("HOÀN TẤT KIỂM PHIẾU.")


if __name__ == "__main__":
    ELECTION_ID_TO_TALLY = 1 
    tally_votes(ELECTION_ID_TO_TALLY)