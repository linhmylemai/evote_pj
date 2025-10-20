# server/check_data.py

import sys
import os
from sqlmodel import Session, select
from typing import List

# Fix đường dẫn để có thể import các modules từ thư mục khác
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import các Models và engine từ server/models/db.py
try:
    from server.models.db import engine, Voter, Account, Candidate, Election, Position
except ImportError:
    print("Lỗi: Không thể import Models. Hãy đảm bảo file db.py nằm trong server/models/")
    sys.exit(1)


def check_database_records():
    """Truy vấn DB để đếm số lượng bản ghi trong các bảng chính."""
    
    print("====================================")
    print("📊 KIỂM TRA SỐ LƯỢNG BẢN GHI TRONG DATABASE")
    print("====================================")
    
    with Session(engine) as session:
        try:
            # Lấy danh sách tất cả các Models cần kiểm tra
            models_to_check = {
                "Cử tri (Voter)": Voter,
                "Tài khoản (Account)": Account,
                "Ứng viên (Candidate)": Candidate,
                "Chức vụ (Position)": Position,
                "Cuộc bầu cử (Election)": Election,
            }

            total_records = 0
            
            for table_name, Model in models_to_check.items():
                # Đếm số lượng bản ghi
                records: List = session.exec(select(Model)).all()
                count = len(records)
                print(f"[{table_name:20}]: {count} bản ghi")
                total_records += count

                # In bản ghi đầu tiên (ví dụ kiểm tra)
                if records:
                    first_record = records[0]
                    # Hiển thị thông tin chính của bản ghi đầu tiên
                    if hasattr(first_record, 'name'):
                         print(f"  -> Ví dụ: ID={first_record.id}, Tên='{first_record.name}'")
                    elif hasattr(first_record, 'name_login'):
                        print(f"  -> Ví dụ: Tên đăng nhập='{first_record.name_login}', Role='{first_record.role}'")


            if total_records > 0:
                print("\n✅ KIỂM TRA THÀNH CÔNG! Dữ liệu đã được nạp vào DB.")
            else:
                print("\n⚠️ CẢNH BÁO: Database đang trống (0 bản ghi). Quá trình tải dữ liệu có thể đã thất bại.")
                print("Vui lòng kiểm tra lại lỗi 'Mã cử tri' trong file load_data_inp.py.")

        except Exception as e:
            print(f"\n❌ LỖI TRUY VẤN DATABASE: {e}")
            print("Đảm bảo file 'evote.db' đã được tạo và chứa các bảng.")


if __name__ == "__main__":
    check_database_records()