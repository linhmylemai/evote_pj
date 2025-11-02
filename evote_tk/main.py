import tkinter as tk
from tkinter import messagebox
import csv, os
from voter_gui import open_voter_window
from admin_gui import open_admin_login

# ======= MÀU CHỦ ĐẠO =======
BG_MAIN = "#fdf6f0"
BTN_VOTER = "#b5651d"
BTN_ADMIN = "#3f3f46"
TXT_DARK = "#3b3b3b"

# ======= ĐƯỜNG DẪN DỮ LIỆU =======
DATA_DIR = os.path.join("..", "server", "data", "input")
ACCOUNT_FILE = os.path.join(DATA_DIR, "tai_khoan.csv")


# ======= HÀM ĐỌC CSV =======
def read_accounts():
    """Đọc file tai_khoan.csv (bỏ qua header lỗi mã hóa)"""
    if not os.path.exists(ACCOUNT_FILE):
        print("⚠️ Không tìm thấy file:", ACCOUNT_FILE)
        return []

    for enc in ("utf-8-sig", "utf-8", "cp1258", "latin-1"):
        try:
            with open(ACCOUNT_FILE, "r", encoding=enc, errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines:
                continue

            rows = []
            for line in lines[1:]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 4:
                    continue
                rows.append({
                    "Tên đăng nhập": parts[0],
                    "Mật khẩu": parts[1],
                    "Vai trò": parts[2].lower(),
                    "Liên kết ID": parts[3]
                })

            print(f"✅ Đọc được {len(rows)} tài khoản bằng encoding: {enc}")
            return rows
        except Exception:
            continue

    print("❌ Không thể đọc file CSV với mọi encoding.")
    return []


# ======= FORM LOGIN =======
def open_login(role, parent):
    parent.withdraw()
    win = tk.Toplevel(parent)
    win.title(f"Đăng nhập {role} — eVote AES+RSA")
    win.geometry("400x320")
    win.configure(bg=BG_MAIN)
    win.resizable(False, False)

    tk.Label(win, text=f"🔐 Đăng nhập {role}", font=("Segoe UI", 18, "bold"),
             bg=BG_MAIN, fg=TXT_DARK).pack(pady=20)

    tk.Label(win, text="Tên đăng nhập:", bg=BG_MAIN, fg=TXT_DARK).pack()
    e_user = tk.Entry(win, width=28, font=("Segoe UI", 11))
    e_user.pack(pady=6)

    tk.Label(win, text="Mật khẩu:", bg=BG_MAIN, fg=TXT_DARK).pack()
    e_pass = tk.Entry(win, width=28, font=("Segoe UI", 11), show="*")
    e_pass.pack(pady=6)

    def do_login():
        u, p = e_user.get().strip(), e_pass.get().strip()
        if not u or not p:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ Tên đăng nhập và Mật khẩu!")
            return

        accounts = read_accounts()
        matched = None

        for acc in accounts:
            if acc["Tên đăng nhập"] == u and acc["Mật khẩu"] == p:
                matched = acc
                break

        if not matched:
            messagebox.showerror("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không đúng!")
            return

        # ---- Đăng nhập ADMIN ----
        if role.lower() == "admin" and matched.get("Vai trò") == "admin":
            messagebox.showinfo("Thành công", f"Xin chào {u} (Admin)!")
            win.destroy()
            open_admin_login(parent)

        # ---- Đăng nhập VOTER ----
        elif role.lower() == "voter" and matched.get("Vai trò") == "user":
            messagebox.showinfo("Thành công", f"Xin chào {u}! Bạn có thể bỏ phiếu.")
            win.destroy()
            open_voter_window(parent, matched.get("Liên kết ID"))

        else:
            messagebox.showerror("Từ chối quyền truy cập", f"Tài khoản {u} không có quyền {role}!")

    # ===== Nút xác nhận đăng nhập =====
    tk.Button(win, text="Đăng nhập", command=do_login,
              bg="#2563eb", fg="white", font=("Segoe UI", 11, "bold"),
              width=18, height=1, relief="flat", cursor="hand2").pack(pady=20)

    def back_main():
        win.destroy()
        parent.deiconify()

    tk.Button(win, text="⬅ Quay lại", command=back_main,
              bg="#6b7280", fg="white", font=("Segoe UI", 11, "bold"),
              width=18, height=1, relief="flat", cursor="hand2").pack()


# ======= MÀN HÌNH CHÍNH =======
def main():
    win = tk.Tk()
    win.title("eVote AES+RSA — Tkinter")
    win.geometry("500x400")
    win.configure(bg=BG_MAIN)

    tk.Label(win, text="🗳 eVote AES+RSA", font=("Segoe UI", 22, "bold"),
             bg=BG_MAIN, fg=TXT_DARK).pack(pady=40)

    # Nút đăng nhập Voter
    tk.Button(win, text="Người bỏ phiếu (Voter)",
              command=lambda: open_login("Voter", win),
              bg=BTN_VOTER, fg="white", font=("Segoe UI", 13, "bold"),
              width=25, height=2, relief="flat", cursor="hand2").pack(pady=20)

    # Nút đăng nhập Admin
    tk.Button(win, text="Quản trị (Admin)",
              command=lambda: open_login("Admin", win),
              bg=BTN_ADMIN, fg="white", font=("Segoe UI", 13, "bold"),
              width=25, height=2, relief="flat", cursor="hand2").pack(pady=10)

    # Nút thoát chương trình
    def exit_app():
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn thoát chương trình không?"):
            win.destroy()

    tk.Button(win, text="🚪 Thoát chương trình",
              command=exit_app,
              bg="#dc2626", fg="white", font=("Segoe UI", 12, "bold"),
              width=25, height=2, relief="flat", cursor="hand2",
              activebackground="#b91c1c").pack(pady=(15, 0))

    win.mainloop()


if __name__ == "__main__":
    main()
