import tkinter as tk
from tkinter import messagebox
import csv, os

# ======= MÀU =======
BG_LOGIN = "#f3f4f6"
TXT_COLOR = "#111827"
BTN_DARK = "#3f3f46"
BTN_DARK_HOVER = "#27272a"
BG_MAIN = "#fdf6f0"

# ======= ĐỌC ADMIN =======
def load_admins():
    path = os.path.join("..", "server", "data", "input", "tai_khoan.csv")
    admins = {}
    if not os.path.exists(path): return admins
    for enc in ("utf-8-sig", "cp1258", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                rows = list(csv.reader(f))
                if not rows: continue
                if "tên" in rows[0][0].lower() or "user" in rows[0][0].lower():
                    rows = rows[1:]
                for r in rows:
                    if len(r) >= 3 and r[2].lower() == "admin":
                        admins[r[0].strip()] = r[1].strip()
                break
        except Exception: pass
    return admins

# ======= DASHBOARD =======
def open_admin_dashboard(parent, username):
    win = tk.Toplevel(parent)
    win.title("Trang quản trị — eVote AES+RSA")
    win.geometry("1000x600")
    win.configure(bg=BG_MAIN)
    tk.Label(win, text=f"Xin chào, {username}", font=("Segoe UI", 14), bg=BG_MAIN).pack(pady=20)
    tk.Label(win, text="Dashboard (đang phát triển...)", font=("Segoe UI", 18, "bold"), bg=BG_MAIN).pack(pady=10)

# ======= LOGIN ADMIN =======
def open_admin_login(parent):
    admins = load_admins()
    win = tk.Toplevel(parent)
    win.title("Admin Login — eVote AES+RSA")
    win.geometry("400x400")
    win.configure(bg=BG_LOGIN)
    win.resizable(False, False)

    frame = tk.Frame(win, bg="white", relief="groove", bd=1)
    frame.place(relx=0.5, rely=0.5, anchor="center", width=300, height=320)

    tk.Label(frame, text="🔒", font=("Segoe UI", 28), bg="white").pack(pady=(25, 8))
    tk.Label(frame, text="Admin Login", font=("Segoe UI", 18, "bold"), bg="white", fg=TXT_COLOR).pack(pady=(0, 20))

    tk.Label(frame, text="Username", bg="white").pack(anchor="w", padx=40)
    entry_user = tk.Entry(frame, font=("Segoe UI", 11), bg="#f3f4f6", relief="flat", justify="center")
    entry_user.pack(padx=40, pady=(3, 10), fill="x")

    tk.Label(frame, text="Password", bg="white").pack(anchor="w", padx=40)
    entry_pass = tk.Entry(frame, font=("Segoe UI", 11), bg="#f3f4f6", relief="flat", show="*", justify="center")
    entry_pass.pack(padx=40, pady=(3, 20), fill="x")

    def handle_login():
        user, pw = entry_user.get().strip(), entry_pass.get().strip()
        if user in admins and admins[user] == pw:
            messagebox.showinfo("Thành công", f"Xin chào {user}, bạn đã đăng nhập!")
            win.destroy()
            open_admin_dashboard(parent, user)
        else:
            messagebox.showerror("Lỗi", "Tên đăng nhập hoặc mật khẩu sai!")

    btn = tk.Button(frame, text="Log in", bg=BTN_DARK, fg="white", font=("Segoe UI", 11, "bold"),
                    relief="flat", command=handle_login)
    btn.pack(pady=5)
