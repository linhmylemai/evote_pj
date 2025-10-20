# common/crypto.py

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import os

# --- 1. Tạo Khóa (Admin Tool sẽ dùng) ---

def generate_rsa_keys():
    """Tạo cặp khóa RSA (Public & Private)"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

def save_private_key(key, path):
    """Lưu Khóa Riêng tư (Admin)"""
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(path, "wb") as f:
        f.write(pem)

def save_public_key(key, path):
    """Lưu Khóa Công khai (Server)"""
    pem = key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(path, "wb") as f:
        f.write(pem)

# Tạo khóa riêng → lấy khóa công khai
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=3072
)
public_key = private_key.public_key()

# Đường dẫn mới
public_path = r"D:\AT&BM HTTT\Project_eVote\server\keys\admin_public_key.pem"
private_path = r"D:\AT&BM HTTT\Project_eVote\admin\keys\admin_private_key.pem"

# Gọi hàm lưu
save_public_key(public_key, public_path)
save_private_key(private_key, private_path)

# --- 2. Mã hóa (Client sẽ dùng) ---

def generate_aes_key():
    """Tạo Khóa AES 256-bit ngẫu nhiên và IV 96-bit cho AES-GCM"""
    return os.urandom(32), os.urandom(12)

def aes_gcm_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """Mã hóa nội dung phiếu bầu bằng AES-GCM (Giữ nguyên)"""
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(iv, plaintext, None)
    return ciphertext_with_tag

def rsa_encrypt(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    ciphertext = public_key.encrypt(
        data,
        padding.PKCS1v15() 
    )
    return ciphertext

# --- 3. Giải mã (Admin Tool sẽ dùng) ---

def rsa_decrypt(private_key: rsa.RSAPrivateKey, ciphertext: bytes) -> bytes:
    plaintext = private_key.decrypt(
        ciphertext,
        padding.PKCS1v15()
    )
    return plaintext

def aes_gcm_decrypt(key: bytes, iv: bytes, ciphertext_with_tag: bytes) -> bytes:
    """Giải mã nội dung phiếu bầu bằng AES-GCM (Giữ nguyên)"""
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext_with_tag, None)
    return plaintext

# --- 4. Xác thực Mật khẩu ---

def hash_password(password: str) -> bytes:
    """Hash mật khẩu bằng bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password: str, hashed_password: bytes) -> bool:
    """Kiểm tra mật khẩu với hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)