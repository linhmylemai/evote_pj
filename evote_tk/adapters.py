import sys, os, json, base64
sys.path.append(os.path.abspath(".."))  # Cho phép import module trong Project_eVote

# ⚠️ TODO: cập nhật đường import theo repo của bạn
# Ví dụ:
# from common.crypto.aes import encrypt_data, decrypt_data
# from common.crypto.rsa import encrypt_key, decrypt_key
# from common.keys import ensure_keys
# Tạm thời mình để code chạy độc lập bằng cryptography:

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEYS_DIR = os.path.join(os.path.dirname(__file__), "data")
PUB_PATH = os.path.join(KEYS_DIR, "public.pem")
PRI_PATH = os.path.join(KEYS_DIR, "private.pem")

def _generate_rsa_keys_if_missing():
    os.makedirs(KEYS_DIR, exist_ok=True)
    if os.path.exists(PUB_PATH) and os.path.exists(PRI_PATH): return
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    with open(PRI_PATH, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(PUB_PATH, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def ensure_keys(): _generate_rsa_keys_if_missing()

def _load_public_key():
    with open(PUB_PATH, "rb") as f: return serialization.load_pem_public_key(f.read())

def _load_private_key():
    with open(PRI_PATH, "rb") as f: return serialization.load_pem_private_key(f.read(), password=None)

def encrypt_vote(vote_obj):
    ensure_keys()
    public_key = _load_public_key()
    aes_key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(aes_key)
    iv = os.urandom(12)
    cipher = aesgcm.encrypt(iv, json.dumps(vote_obj).encode("utf-8"), None)
    enc_key = public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return {
        "enc_key": base64.b64encode(enc_key).decode(),
        "iv": base64.b64encode(iv).decode(),
        "cipher_vote": base64.b64encode(cipher).decode()
    }

def decrypt_vote(enc_obj):
    private_key = _load_private_key()
    aes_key = private_key.decrypt(
        base64.b64decode(enc_obj["enc_key"]),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    aesgcm = AESGCM(aes_key)
    iv = base64.b64decode(enc_obj["iv"])
    cipher = base64.b64decode(enc_obj["cipher_vote"])
    plain = aesgcm.decrypt(iv, cipher, None)
    return json.loads(plain.decode("utf-8"))
