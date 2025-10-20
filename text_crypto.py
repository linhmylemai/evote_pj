# interactive_test_v2.py

import json
import base64
import os
import bcrypt
from common.crypto import (
    generate_rsa_keys,
    rsa_encrypt,
    rsa_decrypt,
    generate_aes_key,
    aes_gcm_encrypt,
    aes_gcm_decrypt,
    serialization
)
from cryptography.hazmat.primitives.asymmetric import rsa

def get_aes_key_input():
    """Lấy Khóa AES từ người dùng (dạng Base64) hoặc tạo ngẫu nhiên."""
    while True:
        choice = input("Bạn muốn (1) Tạo Khóa AES ngẫu nhiên hay (2) Nhập Khóa AES tùy chỉnh (Base64)? (1/2): ")
        if choice == '1':
            aes_key, iv = generate_aes_key()
            print(f"\nKhóa AES ngẫu nhiên được tạo: {base64.b64encode(aes_key).decode()}")
            return aes_key, iv
        
        elif choice == '2':
            # Khóa AES 256-bit là 32 bytes. Base64 của 32 bytes là 44 ký tự.
            key_base64 = input("Nhập Khóa AES tùy chỉnh (44 ký tự Base64): ")
            
            try:
                custom_aes_key = base64.b64decode(key_base64)
                if len(custom_aes_key) != 32:
                    print(f"Lỗi: Độ dài key phải là 32 bytes (nhập {len(custom_aes_key)} bytes). Vui lòng kiểm tra lại Base64.")
                    continue
                
                # Tạo IV ngẫu nhiên (vì IV phải là ngẫu nhiên cho mỗi phiên AES-GCM)
                iv = os.urandom(12) 
                print(f"Khóa AES tùy chỉnh đã được chấp nhận.")
                return custom_aes_key, iv
            except Exception as e:
                print(f"Lỗi khi decode Base64: {e}. Vui lòng nhập đúng định dạng.")
        else:
            print("Lựa chọn không hợp lệ.")


def interactive_test_flow():
    """Chạy luồng mã hóa và giải mã tương tác."""

    print("==================================================")
    print("DEMO LUỒNG MÃ HÓA LAI E-VOTE (CLIENT -> ADMIN)")
    print("==================================================")

    # --- BƯỚC 1: ADMIN TẠO VÀ CUNG CẤP KHÓA CÔNG KHAI ---
    print("\n[SETUP] Admin tạo Khóa RSA (Công khai & Riêng tư) cho phiên demo...")
    admin_private_key, admin_public_key = generate_rsa_keys()
    
    pub_key_pem = admin_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("Khóa Công khai (để Client dùng mã hóa) đã sẵn sàng.")

    # --- BƯỚC 2: CLIENT CHUẨN BỊ VÀ MÃ HÓA ---
    
    # a. Lấy Input Phiếu bầu
    print("\n--------------------------------------------------")
    print("[CLIENT] 🗳️ Vui lòng nhập nội dung phiếu bầu (dạng JSON):")
    while True:
        try:
            plaintext_str = input("Phiếu bầu (JSON): ")
            json.loads(plaintext_str) 
            break
        except json.JSONDecodeError:
            print("Lỗi: Dữ liệu nhập không phải định dạng JSON hợp lệ. Vui lòng thử lại.")
            
    plaintext_vote_bytes = plaintext_str.encode('utf-8')
    
    # b. Lấy Khóa AES từ người dùng (Phần bạn muốn nhập key)
    aes_key, iv = get_aes_key_input()
    
    print("\n[CLIENT]  Bắt đầu mã hóa...")
    
    # c. Mã hóa Phiếu bầu bằng AES-GCM (dùng AES Key và IV)
    cipher_vote_with_tag = aes_gcm_encrypt(aes_key, iv, plaintext_vote_bytes)
    
    # d. Mã hóa Khóa AES bằng RSA Public Key của Admin (enc_key)
    encrypted_aes_key = rsa_encrypt(admin_public_key, aes_key)

    print(" Mã hóa hoàn tất.")
    
    # Dữ liệu gửi lên Server (lưu vào DB)
    data_to_server = {
        "enc_key": encrypted_aes_key.hex(),
        "cipher_vote": cipher_vote_with_tag.hex(),
        "iv": iv.hex()
    }
    
    print("\n[SERVER/DB] 💾 Dữ liệu Phiếu đã mã hóa được lưu trữ:")
    print(f" - Encrypted AES Key (enc_key): {data_to_server['enc_key'][:30]}...")
    print(f" - Ciphertext (cipher_vote):   {data_to_server['cipher_vote'][:30]}...")
    print(f" - IV (iv):                    {data_to_server['iv']}")
    
    # --- BƯỚC 3: ADMIN KIỂM PHIẾU VÀ GIẢI MÃ ---
    
    print("\n--------------------------------------------------")
    input("[ADMIN TOOL]  Bấm Enter để bắt đầu Giải mã (sử dụng Khóa Riêng tư của Admin)...")
    
    # Lấy dữ liệu từ Server/DB và chuyển lại về bytes
    db_enc_key = bytes.fromhex(data_to_server['enc_key'])
    db_cipher_vote = bytes.fromhex(data_to_server['cipher_vote'])
    db_iv = bytes.fromhex(data_to_server['iv'])
    
    # a. Giải mã Khóa AES (dùng RSA Private Key của Admin)
    decrypted_aes_key = rsa_decrypt(admin_private_key, db_enc_key)
    
    # b. Giải mã Phiếu bầu (dùng Khóa AES đã giải mã và IV)
    decrypted_vote_data_bytes = aes_gcm_decrypt(decrypted_aes_key, db_iv, db_cipher_vote)
    
    decrypted_vote_data_str = decrypted_vote_data_bytes.decode('utf-8')
    
    print("Giải mã Khóa AES và Phiếu bầu thành công.")
    print("\n[KẾT QUẢ CUỐI] Phiếu Bầu đã Giải mã:")
    print(decrypted_vote_data_str)

    # --- Xác nhận ---
    if decrypted_vote_data_str == plaintext_str:
        print("\n🎉 THÀNH CÔNG: Dữ liệu giải mã trùng khớp với Phiếu gốc.")
    else:
        print("\n❌ LỖI: Dữ liệu giải mã KHÔNG trùng khớp.")


if __name__ == "__main__":
    interactive_test_flow()