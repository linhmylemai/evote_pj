# common/crypto.py (Đã làm sạch và thêm hàm load)

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
import bcrypt
import os

# --- 1. Quản lý Khóa RSA ---

def generate_rsa_keys(key_size: int = 3072):
    """Tạo cặp khóa RSA (Public & Private)"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
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

def load_private_key(path: str) -> rsa.RSAPrivateKey:
    """Tải Khóa Riêng tư từ file."""
    with open(path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )
    return private_key

def load_public_key(path: str) -> rsa.RSAPublicKey:
    """Tải Khóa Công khai từ file."""
    with open(path, "rb") as f:
        public_key = serialization.load_pem_public_key(
            f.read()
        )
    return public_key

# --- 2. Mã hóa (Client sẽ dùng) ---

def generate_aes_key():
    """Tạo Khóa AES 256-bit ngẫu nhiên và IV 96-bit cho AES-GCM"""
    return os.urandom(32), os.urandom(12)

def rsa_encrypt(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    """Bọc (Encrypt) data (thường là AES key) bằng RSA Public Key (PKCS1v15)"""
    ciphertext = public_key.encrypt(
        data,
        padding.PKCS1v15() 
    )
    return ciphertext

# --- 3. Giải mã (Admin Tool sẽ dùng) ---

def rsa_encrypt(public_key_bytes: bytes, data: bytes):
    """Mã hóa dữ liệu bằng RSA public key"""
    from cryptography.hazmat.backends import default_backend
    # Nạp key từ bytes
    public_key = serialization.load_pem_public_key(
        public_key_bytes, backend=default_backend()
    )
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ciphertext

def aes_gcm_decrypt(key: bytes, iv: bytes, ciphertext_with_tag: bytes) -> bytes:
    """Giải mã nội dung phiếu bầu bằng AES-GCM"""
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext_with_tag, ciphertext_with_tag) # AESGCM.decrypt không cần tag riêng
    return plaintext

# --- 4. Xác thực Mật khẩu ---

def hash_password(password: str) -> bytes:
    """Hash mật khẩu bằng bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password: str, hashed_password: bytes) -> bool:
    """Kiểm tra mật khẩu với hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)