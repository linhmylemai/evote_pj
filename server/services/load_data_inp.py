import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# common/crypto.py
import os
import bcrypt  # 👈 THÊM DÒNG NÀY

import pandas as pd
from sqlmodel import Session
from datetime import datetime
# Import đã hoạt động
from common.crypto import hash_password 
# Import tất cả các model cần thiết
from server.models.db import Voter, Account, Candidate, Position, Election, create_db_and_tables, engine 

# Cấu hình đường dẫn
# BASE_DIR trỏ đến thư mục 'server/' (vì load_data_inp.py nằm trong server/services)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 

# ✅ KHẮC PHỤC LỖI ĐƯỜNG DẪN: Trỏ đến thư mục 'data_input' nằm ngay dưới 'server/'
CSV_DIR = os.path.join(BASE_DIR, "data" ,"input")

# Chuyển đổi chuỗi ngày tháng (dạng 'dd/mm/yyyy' hoặc 'dd-mm-yyyy') thành datetime.date/datetime.datetime
def parse_date(date_str):
    if pd.isna(date_str) or not date_str:
        return None
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(date_str).split(' ')[0], fmt).date() # Lấy date
        except ValueError:
            pass
    return None

def parse_datetime(dt_str):
    if pd.isna(dt_str) or not dt_str:
        return None
    for fmt in ('%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'):
        try:
            return datetime.strptime(str(dt_str), fmt)
        except ValueError:
            pass
    return None

def read_csv_with_fix(filename):
    """Đọc file CSV với encoding utf-8-sig và loại bỏ khoảng trắng thừa ở cột."""
    file_path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}. Vui lòng kiểm tra lại đường dẫn CSV_DIR.")
    
    # ✅ FIX LỖI ENCODING/BOM: Dùng 'utf-8-sig' để xử lý ký tự BOM (thường gây lỗi ở cột đầu tiên)
    df = pd.read_csv(file_path, encoding='utf-8-sig').fillna('')
    # Loại bỏ khoảng trắng thừa ở đầu/cuối tên cột (cũng giúp xử lý ký tự BOM)
    df.columns = df.columns.str.strip()
    return df

def initialize_and_load_data():
    """Tải tất cả dữ liệu CSV vào Database."""
    print("====================================")
    print("BẮT ĐẦU TẢI DỮ LIỆU BAN ĐẦU")
    print("====================================")
    
    try:
        create_db_and_tables()
    except Exception:
        pass

    with Session(engine) as session:
        try:
            # --- 1. Tải Cử tri (Voter) ---
            print("1. Đang tải dữ liệu Cử tri (Voter) & Tài khoản (Account)...")
            
            # ✅ SỬ DỤNG HÀM READ CSV ĐÃ SỬA
            df_voters = read_csv_with_fix('cu_tri.csv')
            df_accounts = read_csv_with_fix('tai_khoan.csv')
            
            voter_map = {} 

            for index, row in df_voters.iterrows():
                # Tên cột đã được xác nhận chính xác
                voter = Voter(
                    cccd=str(row['CCCD']), 
                    name=row['Họ và tên'],
                    date_of_birth=parse_date(row['Ngày sinh']),
                    email=row['Email'],
                    phone_number=row['SĐT'],
                    address=row['Địa chỉ'],
                )
                session.add(voter)
                session.flush() 
                voter_map[row['Mã cử tri']] = voter.id # KHÔNG CÒN LỖI KEY ERROR

            # Tải Tài khoản sau khi đã có Voter ID
            for index, row in df_accounts.iterrows():
                voter_db_id = voter_map.get(row['Liên kết ID']) # Sử dụng Mã cử tri
                if voter_db_id is not None:
                    # Hash mật khẩu
                    hashed_pw = hash_password(str(row['Mật khẩu']))

                    account = Account(
                        name_login=row['Tên đăng nhập'], 
                        password_hash=hashed_pw.decode('utf-8'),
                        role=row['Vai trò'],
                        voter_id=voter_db_id,
                        has_voted=False 
                    )
                    session.add(account)
            
            print(f"✅ Tải {len(df_voters)} Cử tri và {len(df_accounts)} Tài khoản thành công.")


            # --- 2. Tải Cuộc bầu cử (Election) ---
            print("2. Đang tải dữ liệu Cuộc bầu cử (Election)...")
            df_elections = read_csv_with_fix('cuoc_bau.csv')
            election_map = {}

            for index, row in df_elections.iterrows():
                election = Election(
                    name=row['Tiêu đề'],
                    start_time=parse_datetime(row['Thời gian bắt đầu']),
                    end_time=parse_datetime(row['Thời gian kết thúc']),
                )
                session.add(election)
                session.flush()
                election_map[row['Mã cuộc bầu']] = election.id 
            print(f"✅ Tải {len(df_elections)} Cuộc bầu cử thành công.")
            
            
            # --- 3. Tải Ứng viên (Candidate) và Chức vụ (Position) ---
            print("3. Đang tải dữ liệu Ứng viên (Candidate) và Chức vụ (Position)...")
            df_candidates = read_csv_with_fix('ung_vien.csv')
            df_positions = read_csv_with_fix('chuc_vu.csv')

            candidate_map = {}

            # Tải Ứng viên (Cột: Mã ứng viên, Họ và tên)
            for index, row in df_candidates.iterrows():
                candidate = Candidate(
                    name=row['Họ và tên'],
                )
                session.add(candidate)
                session.flush()
                candidate_map[row['Mã ứng viên']] = candidate.id

            # Tải Chức vụ (Cột: Mã chức vụ, Chức vụ, Mã ứng viên)
            for index, row in df_positions.iterrows():
                candidate_db_id = candidate_map.get(row['Mã ứng viên'])
                
                # Giả định: Lấy Mã cuộc bầu từ CSV (Nếu có) hoặc mặc định là ID 1
                election_id_from_csv = row.get('Mã cuộc bầu')
                final_election_id = election_map.get(election_id_from_csv, 1)

                if candidate_db_id is not None:
                    position = Position(
                        name=row['Chức vụ'],
                        candidate_id=candidate_db_id,
                        election_id=final_election_id
                    )
                    session.add(position)
            
            print(f"✅ Tải {len(df_candidates)} Ứng viên và {len(df_positions)} Chức vụ thành công.")
            
            
            # Commit tất cả thay đổi
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"\n❌ LỖI NGHIÊM TRỌNG KHI TẢI DỮ LIỆU: {e}")
            print("Vui lòng kiểm tra lại cấu trúc các file CSV và định dạng ngày tháng.")

    print("\n====================================")
    print("HOÀN TẤT TẢI DỮ LIỆU VÀO DATABASE")
    print("====================================")

if __name__ == "__main__":
    initialize_and_load_data()