# test_cast_vote.py

import os
import sys
import json
import base64
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import load_pem_public_key

# Thêm đường dẫn thư mục gốc để import common/crypto
# Giả định script này nằm ở thư mục gốc Project_eVote
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import các hàm từ file crypto.py của bạn
from common.crypto import load_public_key, generate_aes_key, rsa_encrypt

# --- 1. CẤU HÌNH VÀ HÀM HỖ TRỢ ---

# URL Server
BASE_URL = "http://127.0.0.1:8000"

# Đường dẫn đến Khóa Công khai của Admin
# Giả định Public Key nằm tại Project_eVote/server/keys/admin_public_key.pem
PUBLIC_KEY_PATH = os.path.join(os.path.dirname(__file__), "server", "keys", "admin_public_key.pem")

# Hàm mã hóa AES-GCM (Dùng cho Client)
def aes_gcm_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """Mã hóa nội dung phiếu bầu bằng AES-GCM"""
    aesgcm = AESGCM(key)
    # Ghi chú: AES-GCM trong Python trả về ciphertext + tag (đã gộp)
    ciphertext_with_tag = aesgcm.encrypt(iv, plaintext, None)
    return ciphertext_with_tag


def run_cast_test(ballot_token: str):
    """Thực hiện quá trình mã hóa phiếu bầu và gửi yêu cầu POST /api/cast"""
    print("--- BẮT ĐẦU MÔ PHỎNG CLIENT VÀ TEST CAST VOTE ---")

    # 1. Dữ liệu Phiếu bầu (Payload sẽ gửi)
    # Giả định cử tri bầu cho Ứng viên có ID=3 trong Cuộc bầu cử ID=1
    VOTE_PAYLOAD = {
        "candidate_id": 3,
        "election_id": 1
    }
    vote_plaintext_bytes = json.dumps(VOTE_PAYLOAD).encode('utf-8')
    print(f"Phiếu bầu thô: {VOTE_PAYLOAD}")

    # 2. Tải Khóa Công khai của Admin
    try:
        admin_public_key = load_public_key(PUBLIC_KEY_PATH)
        print("✅ Tải Khóa Công khai RSA thành công.")
    except Exception as e:
        print(f"❌ Lỗi tải Khóa Công khai. Đảm bảo file {PUBLIC_KEY_PATH} tồn tại và hợp lệ.")
        print(f"Chi tiết lỗi: {e}")
        return

    # 3. Sinh Khóa AES ngẫu nhiên
    aes_key, iv = generate_aes_key()
    print("✅ Sinh Khóa AES và IV ngẫu nhiên thành công.")

    # 4. Mã hóa Phiếu bầu bằng AES-GCM
    cipher_vote_bytes = aes_gcm_encrypt(aes_key, iv, vote_plaintext_bytes)
    print("✅ Mã hóa Phiếu bầu (cipher_vote) thành công.")

    # 5. Mã hóa Khóa AES bằng RSA Public Key (Khóa bọc)
    enc_key_bytes = rsa_encrypt(admin_public_key, aes_key)
    print("✅ Mã hóa Khóa AES (enc_key) bằng RSA thành công.")

    # 6. Chuyển đổi sang chuỗi Base64
    enc_key_b64 = base64.b64encode(enc_key_bytes).decode('utf-8')
    cipher_vote_b64 = base64.b64encode(cipher_vote_bytes).decode('utf-8')
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    print("✅ Chuyển đổi Base64 hoàn tất.")

    # 7. Chuẩn bị Payload cho API /api/cast
    cast_payload = {
        "ballot_token": ballot_token,
        "enc_key": enc_key_b64,
        "cipher_vote": cipher_vote_b64,
        "iv": iv_b64
    }

    print("\n--- JSON PAYLOAD SẴN SÀNG ---")
    print(json.dumps(cast_payload, indent=2))
    print("------------------------------\n")

    # 8. Gửi yêu cầu POST tới /api/cast
    cast_url = f"{BASE_URL}/api/cast"
    print(f"Đang gửi yêu cầu POST tới: {cast_url}")
    
    try:
        response = requests.post(cast_url, json=cast_payload)
        response.raise_for_status() # Ném lỗi nếu status code là 4xx hoặc 5xx
        
        print("\n=== KẾT QUẢ CAST VOTE THÀNH CÔNG ===")
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        print("====================================")
        
    except requests.exceptions.HTTPError as err:
        print(f"\n❌ LỖI KHI GỬI CAST VOTE. Status Code: {err.response.status_code}")
        print(f"Chi tiết lỗi từ Server: {err.response.json().get('detail', 'Không có chi tiết lỗi.')}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ LỖI KẾT NỐI: Đảm bảo server đang chạy tại {BASE_URL}.")
        print(f"Chi tiết lỗi: {e}")

# --- THỰC THI SCRIPT ---

if __name__ == "__main__":
    # --- BƯỚC CẦN THIẾT: THAY THẾ TOKEN NÀY ---
    # 🚨 Bạn PHẢI lấy token từ API /api/login trước khi chạy script này
    # Ví dụ: 3ER2kTXiqFKOLV4GaWDQ7-nX5D2QZPU...
    MY_BALLOT_TOKEN = "o1lK53K2dSvIPFTk7VGHyCrKmi1P6P0hRu12MqF8wp4" 
    
    if MY_BALLOT_TOKEN == "TOKEN_NHẬN_ĐƯỢC_TỪ_API_LOGIN":
        print("🚨 LỖI: Vui lòng thay thế MY_BALLOT_TOKEN bằng token hợp lệ từ API /api/login trước khi chạy.")
    else:
        run_cast_test(MY_BALLOT_TOKEN)