import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import sys
import voter_gui
import admin_gui



# ===== MÀU CHỦ ĐẠO =====
BG_MAIN = "#fdf6f0"
BTN_VOTER = "#b5651d"
BTN_ADMIN = "#3f3f46"
TXT_DARK = "#3b3b3b"
BTN_BLUE = "#2563eb"

# ===== ĐƯỜNG DẪN CSV =====
# ĐƯỜNG DẪN CHUẨN TỚI FILE CSV
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_FILE = os.path.join(BASE_DIR, "..", "server", "data", "input", "tai_khoan.csv")

# ===== DANH SÁCH CÁC ĐƯỜNG DẪN KHẢ DĨ =====
FALLBACK_PATHS = [
    ACCOUNT_FILE,
    os.path.join(os.path.dirname(__file__), "tai_khoan.csv"),
    os.path.join(os.getcwd(), "tai_khoan.csv"),
    "/mnt/data/tai_khoan.csv",
]
# ===== HÀM ĐỌC FILE TÀI KHOẢN (file bạn bị lỗi mã hóa latin-1) =====
# ===== HÀM ĐỌC FILE TÀI KHOẢN (thử nhiều đường dẫn và mã hoá, chuẩn hoá header) =====
import unicodedata

# các đường dẫn khả dĩ để tìm file
FALLBACK_PATHS = [
    ACCOUNT_FILE,                            # đường dẫn hiện tại trong file
    os.path.join(os.path.dirname(__file__), "tai_khoan.csv"),  # cùng thư mục với main.py
    os.path.join(os.getcwd(), "tai_khoan.csv"),                # cwd khi chạy
    "/mnt/data/tai_khoan.csv",               # nơi upload trong môi trường notebook
]

# mapping các header tiếng Việt/phức tạp -> key chuẩn
HEADER_MAP = {
    "tendangnhap": "username", "tên đăng nhập": "username", "tên_đăng_nhập": "username",
    "tên": "username", "username": "username",
    "matkhau": "password", "mật khẩu": "password", "mật_khẩu": "password",
    "mật": "password", "password": "password",
    "vaitro": "role", "vai trò": "role", "vai_trò": "role", "vai": "role", "role": "role",
}

def _normalize_header(h: str) -> str:
    # loại bỏ BOM, unicode normal, chỉ lấy chữ thường, thay dấu nối bằng space
    if h is None:
        return ""
    s = h.strip()
    # remove BOM and normalize
    s = s.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    s = unicodedata.normalize("NFKD", s)
    # lowercase and remove diacritics
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().replace("-", " ").replace("_", " ").strip()
    # collapse spaces
    s = " ".join(s.split())
    return s

def read_accounts():
    import csv, unicodedata

    # tìm file trong danh sách khả dĩ
    path_used = None
    for p in FALLBACK_PATHS:
        if os.path.exists(p):
            path_used = p
            break
    if not path_used:
        print("⚠ Không tìm thấy file tai_khoan.csv")
        return []

    # thử nhiều mã hóa
    encodings = ["utf-8-sig", "utf-8", "cp1258", "latin-1"]
    lines = None
    for enc in encodings:
        try:
            with open(path_used, "r", encoding=enc, errors="ignore") as f:
                raw = f.read().strip()
            if raw:
                lines = [l.strip() for l in raw.replace("\r\n", "\n").split("\n") if l.strip()]
                break
        except Exception as e:
            continue
    if not lines:
        print("⚠ Không đọc được nội dung file.")
        return []

    # chuẩn hóa text (loại dấu, ký tự lạ)
    def normalize(s):
        s = s.replace("\ufeff", "").strip()  # bỏ BOM
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return s.lower().replace("_", " ").replace("-", " ")

    header_raw = [normalize(h) for h in lines[0].split(",")]
    header_map = {}
    for i, h in enumerate(header_raw):
        if "ten" in h and "nhap" in h:
            header_map[i] = "username"
        elif "mat" in h and "khau" in h:
            header_map[i] = "password"
        elif "vai" in h and ("tro" in h or "role" in h):
            header_map[i] = "role"
        else:
            header_map[i] = f"col{i}"

    accounts = []
    for line in lines[1:]:
        cols = [c.strip() for c in line.split(",")]
        row = {"username": "", "password": "", "role": ""}
        for i, val in enumerate(cols):
            key = header_map.get(i)
            if key in row:
                row[key] = val
        if row["username"] and row["password"]:
            accounts.append(row)

    print(f"DEBUG >>> Đọc được {len(accounts)} tài khoản")
    if accounts:
        print("DEBUG >>> Mẫu:", accounts[:3])
    return accounts



# ===== APP CHÍNH =====
def main():
    win = tk.Tk()
    win.title("eVote AES+RSA — Tkinter")
    win.geometry("500x400")
    win.configure(bg=BG_MAIN)
    win.resizable(False, False)

    # Frame chính
    frame_main = tk.Frame(win, bg=BG_MAIN)
    frame_login = tk.Frame(win, bg=BG_MAIN)
    frame_main.pack(fill="both", expand=True)

    # ===== GIAO DIỆN TRANG CHÍNH =====
    tk.Label(frame_main, text="🗳 eVote AES+RSA",
             font=("Segoe UI", 22, "bold"), bg=BG_MAIN, fg=TXT_DARK).pack(pady=40)

    tk.Button(frame_main, text="Người bỏ phiếu (Voter)",
              bg=BTN_VOTER, fg="white", font=("Segoe UI", 13, "bold"),
              width=25, height=2, relief="flat",
              command=lambda: open_login("Voter")).pack(pady=15)

    tk.Button(frame_main, text="Quản trị (Admin)",
              bg=BTN_ADMIN, fg="white", font=("Segoe UI", 13, "bold"),
              width=25, height=2, relief="flat",
              command=lambda: open_login("Admin")).pack(pady=10)

    tk.Button(frame_main, text="🚪 Thoát chương trình",
              bg="#dc2626", fg="white", font=("Segoe UI", 12, "bold"),
              width=25, height=2, relief="flat",
              command=win.destroy).pack(pady=30)

    # ===== GIAO DIỆN ĐĂNG NHẬP =====
    lbl_title = tk.Label(frame_login, text="", font=("Segoe UI", 20, "bold"),
                         bg=BG_MAIN, fg=TXT_DARK)
    lbl_title.pack(pady=30)

    tk.Label(frame_login, text="Tên đăng nhập:", bg=BG_MAIN, fg=TXT_DARK).pack()
    e_user = tk.Entry(frame_login, width=28, font=("Segoe UI", 11))
    e_user.pack(pady=6)

    tk.Label(frame_login, text="Mật khẩu:", bg=BG_MAIN, fg=TXT_DARK).pack()
    e_pass = tk.Entry(frame_login, width=28, font=("Segoe UI", 11), show="*")
    e_pass.pack(pady=6)

    def do_login():
        role_view = lbl_title.cget("text").split()[-1].lower()
        u, p = e_user.get().strip(), e_pass.get().strip()
        if not u or not p:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đủ tên và mật khẩu!")
            return

        accounts = read_accounts()
        print("DEBUG >>> Accounts loaded:", accounts)
        print("DEBUG >>> Trying login with:", u, p)

        if not accounts:
            messagebox.showerror("Lỗi dữ liệu", "Không đọc được file tài khoản.")
            return

        matched = None
        for acc in accounts:
            username = acc.get("username", "").strip()
            password = acc.get("password", "").strip()
            role = acc.get("role", "").strip().lower()
            print("DEBUG >>> Comparing:", username, password, role)  # dòng debug tạm

            if username == u and password == p:
                matched = {"username": username, "role": role}
                break



        if not matched:
            messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng!")
            return

        if role_view == "admin" and matched["role"] == "admin":
            messagebox.showinfo("Thành công", f"Xin chào {u} (Admin)!")
    # ✅ Mở giao diện admin_gui
            admin_gui.open_admin_login(win)

        elif role_view == "voter" and matched["role"] in ("user", "voter"):
            messagebox.showinfo("Thành công", f"Xin chào {u}! Bạn có thể bỏ phiếu.")
    # ✅ Mở giao diện voter_gui
            voter_gui.open_voter_window(win, u)




    # ===== NÚT ĐĂNG NHẬP + QUAY LẠI =====
    tk.Button(frame_login, text="Đăng nhập", command=do_login,
              bg=BTN_BLUE, fg="white", font=("Segoe UI", 11, "bold"),
              width=18, relief="flat").pack(pady=20)

    tk.Button(frame_login, text="⬅ Quay lại",
              bg="#6b7280", fg="white", font=("Segoe UI", 11, "bold"),
              width=18, relief="flat",
              command=lambda: switch(frame_login, frame_main)).pack()

    # ===== CHUYỂN FRAME =====
    def open_login(role):
        e_user.delete(0, tk.END)
        e_pass.delete(0, tk.END)
        lbl_title.config(text=f"🔐 Đăng nhập {role}")
        switch(frame_main, frame_login)

    def switch(hide, show):
        hide.pack_forget()
        show.pack(fill="both", expand=True)

    win.mainloop()


# ===== CHẠY ỨNG DỤNG =====
if __name__ == "__main__":
    print(">>> eVote GUI khởi động thành công ✅")
    main()
