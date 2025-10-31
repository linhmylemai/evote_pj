import tkinter as tk
from voter_gui import open_voter_window
from admin_gui import open_admin_login

# ======= MÀU CHỦ ĐẠO =======
BG_MAIN = "#fdf6f0"
BTN_VOTER = "#b5651d"
BTN_ADMIN = "#3f3f46"

def main():
    root = tk.Tk()
    root.title("eVote AES+RSA — Tkinter")
    root.geometry("500x400")
    root.configure(bg=BG_MAIN)

    tk.Label(root, text="🗳 eVote AES+RSA", font=("Segoe UI", 22, "bold"), bg=BG_MAIN, fg="#3b3b3b").pack(pady=40)

    # Người bỏ phiếu
    tk.Button(
        root, text="Người bỏ phiếu (Voter)",
        command=lambda: open_voter_window(root, "user001"),
        bg=BTN_VOTER, fg="white", font=("Segoe UI", 13, "bold"),
        width=25, height=2, relief="flat"
    ).pack(pady=20)

    # Quản trị
    tk.Button(
        root, text="Quản trị (Admin)",
        command=lambda: open_admin_login(root),
        bg=BTN_ADMIN, fg="white", font=("Segoe UI", 13, "bold"),
        width=25, height=2, relief="flat"
    ).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
