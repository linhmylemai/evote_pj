import tkinter as tk
from adapters import ensure_keys
from admin_gui import open_admin_window
from voter_gui import open_voter_window

BG = "#f1e9d2"
BTN1 = "#b45309"
BTN2 = "#3f3f46"

def main():
    ensure_keys()
    root = tk.Tk()
    root.title("eVote AES+RSA — Tkinter")
    root.geometry("420x280")
    root.configure(bg=BG)

    tk.Label(root, text="🗳 eVote AES+RSA", font=("Segoe UI", 18, "bold"), bg=BG).pack(pady=20)

    tk.Button(root, text="Người bỏ phiếu (Voter)", width=25, height=2,
              bg=BTN1, fg="white", font=("Segoe UI", 11, "bold"),
              command=lambda: open_voter_window(root)).pack(pady=10)

    tk.Button(root, text="Quản trị (Admin)", width=25, height=2,
              bg=BTN2, fg="white", font=("Segoe UI", 11, "bold"),
              command=lambda: open_admin_window(root)).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
