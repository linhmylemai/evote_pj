import tkinter as tk
from tkinter import messagebox
import csv, json, os, base64
from adapters import encrypt_vote, ensure_keys
from common.crypto import rsa_encrypt, generate_aes_key



# ======= MÀU CHỦ ĐẠO =======
BG_MAIN = "#fdf6f0"        # kem pastel
BG_HEADER = "#b5838d"      # hồng nâu pastel
BG_CARD = "#f4ede4"        # nền ô ứng viên
BTN_PRIMARY = "#8ecae6"    # xanh pastel
TXT_DARK = "#3f3f46"

# ======= ĐỌC DỮ LIỆU =======
def load_accounts():
    path = os.path.join("..", "server", "data", "input", "tai_khoan.csv")
    accounts = {}
    if not os.path.exists(path):
        return accounts

    tried_rows = []
    for enc in ("utf-8-sig", "cp1258", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                rows = list(csv.reader(f))
                if rows:
                    tried_rows = rows
                    break
        except Exception:
            pass

    if not tried_rows:
        return accounts

    rows = tried_rows

    def looks_like_header(first_cell: str) -> bool:
        s = (first_cell or "").strip().lower()
        return any(k in s for k in ["tên", "dang", "user", "mật", "mat", "tk"]) and len(s) > 3

    start = 1 if rows and rows[0] and looks_like_header(rows[0][0]) else 0

    for r in rows[start:]:
        if len(r) < 2:
            continue
        u = (r[0] or "").strip()
        p = (r[1] or "").strip()
        if u:
            accounts[u] = p
    return accounts


def load_candidates():
    path = os.path.join("..", "server", "data", "input", "ung_vien.csv")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)

# ======= GỬI PHIẾU =======
def submit_vote(selected_candidate, voter_name, win):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import base64, os

    if not selected_candidate.get():
        messagebox.showwarning("⚠️ Chưa chọn", "Vui lòng chọn một ứng viên trước khi gửi phiếu!")
        return

    ensure_keys()

    # 1️⃣ Chuẩn bị dữ liệu bỏ phiếu
    vote_data = {
        "voter": voter_name,
        "candidate": selected_candidate.get()
    }
    plaintext = json.dumps(vote_data).encode("utf-8")

    # 2️⃣ Mã hóa AES-GCM
    aes_key = os.urandom(32)
    iv = os.urandom(12)
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    # 3️⃣ Mã hóa AES key bằng RSA
    public_key_path = os.path.join("data", "public.pem")
    with open(public_key_path, "rb") as f:
        public_key = f.read()

    from common.crypto import rsa_encrypt
    encrypted_aes_key = rsa_encrypt(public_key, aes_key)

    # 4️⃣ Ghi vào file JSON
    record = {
        "voter": voter_name,
        "candidate": selected_candidate.get(),
        "iv": base64.b64encode(iv).decode(),
        "aes_key": base64.b64encode(encrypted_aes_key).decode(),
        "encrypted_vote": base64.b64encode(ciphertext).decode(),
    }

    path = os.path.join("evote_tk", "data", "votes_encrypted.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    existing = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    # 5️⃣ Thông báo pastel đẹp
    popup = tk.Toplevel(win)
    popup.title("🎉 Thành công")
    popup.geometry("300x150")
    popup.configure(bg="#fef6e4")

    tk.Label(popup, text="🎉 Phiếu bầu của bạn\nđã được ghi nhận!",
             font=("Segoe UI", 13, "bold"), bg="#fef6e4", fg="#333").pack(pady=20)
    tk.Button(popup, text="Đóng", command=popup.destroy,
              bg="#4CAF50", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(pady=10)

    selected_candidate.set("")  # reset



# ======= FORM BỎ PHIẾU =======
def open_vote_window(parent, voter_name):
    win = tk.Toplevel(parent)
    win.title("🗳 Bỏ phiếu điện tử — eVote AES+RSA")
    win.geometry("1000x700")
    win.configure(bg=BG_MAIN)

    tk.Label(win, text="🗳 BỎ PHIẾU ĐIỆN TỬ", font=("Segoe UI", 26, "bold"),
             bg=BG_MAIN, fg=BG_HEADER).pack(pady=(30, 10))
    tk.Label(win, text=f"Xin chào, {voter_name}", font=("Segoe UI", 12),
             bg=BG_MAIN, fg=TXT_DARK).pack(pady=(0, 15))
    tk.Label(win, text="Chọn một ứng viên bạn muốn bầu", font=("Segoe UI", 13),
             bg=BG_MAIN, fg=TXT_DARK).pack(pady=(0, 10))

    container = tk.Canvas(win, bg=BG_MAIN, highlightthickness=0)
    frame = tk.Frame(container, bg=BG_MAIN)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=container.yview)
    container.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    container.pack(side="left", fill="both", expand=True)
    container.create_window((0, 0), window=frame, anchor="nw")

    def on_configure(event):
        container.configure(scrollregion=container.bbox("all"))
    frame.bind("<Configure>", on_configure)

    selected = tk.StringVar()
    candidates = load_candidates()

    if not candidates:
        tk.Label(frame, text="Không có dữ liệu ứng viên", bg=BG_MAIN, fg="red").pack(pady=20)
        return

    for i, c in enumerate(candidates):
        ma_uv = c.get("Mã ứng viên", "")
        ten = c.get("Họ và tên", "")
        card = tk.Frame(frame, bg=BG_CARD, relief="flat", bd=2)
        card.pack(fill="x", padx=80, pady=8, ipady=10)
        tk.Radiobutton(card, text=f"{ten} ({ma_uv})", variable=selected,
                       value=ten, bg=BG_CARD, fg=TXT_DARK,
                       font=("Segoe UI", 13, "bold"), selectcolor=BG_CARD,
                       indicatoron=False, width=35, pady=8,
                       activebackground="#eadbd4", relief="ridge").pack(side="left", padx=25)

    tk.Button(win, text="GỬI PHIẾU BẦU", 
          command=lambda: submit_vote(selected, voter_name, win),
          font=("Segoe UI", 14, "bold"), 
          bg=BTN_PRIMARY, fg="white",
          activebackground="#219ebc", relief="flat", padx=30, pady=10
          ).pack(pady=30)


# ======= FORM ĐĂNG NHẬP =======
def open_voter_window(parent):
    login = tk.Toplevel(parent)
    login.title("Đăng nhập cử tri — eVote AES+RSA")
    login.geometry("400x380")
    login.configure(bg="#f4f4f4")

    tk.Label(login, text="🔒", font=("Segoe UI", 40), bg="#f4f4f4").pack(pady=(30, 10))
    tk.Label(login, text="Đăng nhập để bỏ phiếu", font=("Segoe UI", 16, "bold"),
             bg="#f4f4f4", fg="#333").pack(pady=(0, 30))

    tk.Label(login, text="Tên đăng nhập", bg="#f4f4f4").pack(anchor="w", padx=60)
    entry_user = tk.Entry(login, width=30, font=("Segoe UI", 12))
    entry_user.pack(pady=5)

    tk.Label(login, text="Mật khẩu", bg="#f4f4f4").pack(anchor="w", padx=60)
    entry_pass = tk.Entry(login, show="*", width=30, font=("Segoe UI", 12))
    entry_pass.pack(pady=5)

    def handle_login():
        accounts = load_accounts()
        user = entry_user.get().strip()
        pw = entry_pass.get().strip()
        if user in accounts and accounts[user] == pw:
            messagebox.showinfo("Thành công", f"Xin chào {user}, bạn có thể bỏ phiếu!")
            login.destroy()
            open_vote_window(parent, user)
        else:
            messagebox.showerror("Lỗi", "Tên đăng nhập hoặc mật khẩu sai!")

    tk.Button(login, text="Đăng nhập", command=handle_login,
              bg="#1d4ed8", fg="white", font=("Segoe UI", 12, "bold"),
              relief="flat", padx=20, pady=5).pack(pady=25)
