import tkinter as tk
from tkinter import ttk, messagebox
import csv, os
from datetime import datetime

# ⚙️ Ngăn Tkinter tự tạo root khi import
_root = tk.Tk()
_root.withdraw()

# ===== STYLE =====
BG_MAIN = "#fdf6f0"
BG_CARD = "#f4ede4"
TXT_DARK = "#111827"
BTN_PRIMARY = "#2563eb"
BTN_GRAY = "#9ca3af"
BTN_HOVER = "#1d4ed8"

DATA_DIR = os.path.join("..", "server", "data", "input")

# ===== Helper: đọc file CSV =====
def read_csv(path):
    for enc in ("utf-8-sig", "utf-8", "cp1258", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    return rows
        except Exception:
            continue
    return []

# ===== Helper: ghi CSV append =====
def append_csv(path, row, headers):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# ===== Giao diện BỎ PHIẾU =====
def open_voter_window(parent, voter_id):
    parent.withdraw()
    win = tk.Toplevel()
    win.title("Bỏ phiếu điện tử — eVote AES+RSA")
    win.geometry("950x650")
    win.configure(bg=BG_MAIN)

    # ===== HEADER =====
    tk.Label(win, text="🗳 BỎ PHIẾU ĐIỆN TỬ",
             font=("Segoe UI", 22, "bold"), bg=BG_MAIN, fg="#b5651d").pack(pady=(20, 5))
    tk.Label(win, text=f"Xin chào, {voter_id}",
             font=("Segoe UI", 11), bg=BG_MAIN, fg=TXT_DARK).pack(pady=(0, 15))

    # ===== SCROLLABLE FRAME =====
    outer = tk.Frame(win, bg=BG_MAIN)
    outer.pack(fill="both", expand=True, padx=20, pady=10)

    canvas = tk.Canvas(outer, bg=BG_MAIN, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=BG_MAIN)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ===== LOAD DỮ LIỆU =====
    chuc_vu = read_csv(os.path.join(DATA_DIR, "chuc_vu.csv"))
    ung_vien = read_csv(os.path.join(DATA_DIR, "ung_vien.csv"))
    cuoc_bau = read_csv(os.path.join(DATA_DIR, "cuoc_bau.csv"))

    ma_cuoc_bau = cuoc_bau[0]["Mã cuộc bầu"] if cuoc_bau else "CB001"

    # Map mã ứng viên -> họ tên
    name_map = {u["Mã ứng viên"]: u["Họ và tên"] for u in ung_vien if u.get("Mã ứng viên")}

    # Gom ứng viên theo chức vụ
    grouped = {}
    for row in chuc_vu:
        pos = row.get("Chức vụ", "Khác").strip()
        uv = row.get("Mã ứng viên", "").strip()
        if pos and uv:
            grouped.setdefault(pos, []).append(uv)

    selections = {}  # {chức vụ: tk.StringVar}

        # ===== HIỂN THỊ CHỨC VỤ THEO 2 CỘT =====
    pos_list = list(grouped.items())
    cols = 2
    grid_roles = tk.Frame(scroll_frame, bg=BG_MAIN)
    grid_roles.pack(fill="x", padx=20, pady=10)

    for i, (pos, uvs) in enumerate(pos_list):
        # ==== CARD CHỨC VỤ ====
        role_card = tk.Frame(grid_roles, bg=BG_MAIN)
        role_card.grid(row=i // cols, column=i % cols, padx=20, pady=10, sticky="n")

        # Tiêu đề chức vụ
        tk.Label(role_card, text=pos.upper(),
                 font=("Segoe UI", 15, "bold"), bg=BG_MAIN, fg="#b5651d").pack(anchor="center", pady=(5, 10))

        var = tk.StringVar()
        selections[pos] = var

        # ==== DANH SÁCH ỨNG VIÊN ====
        for uid in uvs:
            name = name_map.get(uid, f"Ứng viên {uid}")
            card = tk.Frame(role_card, bg=BG_CARD, bd=1, relief="solid", width=350, height=75)
            card.pack(padx=10, pady=6)
            card.pack_propagate(False)

            tk.Label(card, text=name, font=("Segoe UI", 13, "bold"),
                     bg=BG_CARD, fg=TXT_DARK, anchor="w").pack(anchor="w", padx=15, pady=(8, 0))
            tk.Label(card, text=f"ID: {uid}", bg=BG_CARD,
                     fg="#6b7280", font=("Segoe UI", 10)).pack(anchor="w", padx=15)
            tk.Radiobutton(card, text="Chọn", variable=var, value=uid,
                           bg=BG_CARD, font=("Segoe UI", 11),
                           activebackground=BG_CARD).pack(anchor="e", padx=15, pady=(0, 5))


    # ===== NÚT DƯỚI =====
    bottom = tk.Frame(win, bg=BG_MAIN)
    bottom.pack(fill="x", pady=15)

    # ===== GỬI PHIẾU =====
    def submit_vote():
        result = {pos: var.get() for pos, var in selections.items()}
        if any(v == "" for v in result.values()):
            messagebox.showwarning("Thiếu lựa chọn", "Vui lòng chọn ứng viên cho tất cả chức vụ!")
            return

        # Sinh mã phiếu
        phieu_raw_path = os.path.join(DATA_DIR, "phieu_bau_raw.csv")
        phieu_sach_path = os.path.join(DATA_DIR, "phieu_bau_sach.csv")

        existing = read_csv(phieu_raw_path)
        next_id = len(existing) + 1
        ma_phieu_base = f"PB{next_id:03d}"

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Lưu mỗi chức vụ là 1 phiếu riêng
        for idx, (pos, uid) in enumerate(result.items(), start=1):
            ma_phieu = f"{ma_phieu_base}_{idx:02d}"
            row = {
                "Mã phiếu": ma_phieu,
                "Mã cuộc bầu": ma_cuoc_bau,
                "Mã cử tri": voter_id,
                "Mã ứng viên": uid,
                "Thời điểm bỏ phiếu": now,
                "Hợp lệ": "True"
            }
            append_csv(phieu_raw_path, row, row.keys())
            append_csv(phieu_sach_path, row, row.keys())

        messagebox.showinfo("Gửi phiếu thành công ✅",
                            "Phiếu của bạn đã được ghi nhận vào hệ thống!")
        win.destroy()
        parent.deiconify()

    tk.Button(bottom, text="Đóng", bg=BTN_GRAY, fg="white",
              font=("Segoe UI", 11, "bold"), width=10, relief="flat",
              command=lambda: (win.destroy(), parent.deiconify())).pack(side="right", padx=10)

    tk.Button(bottom, text="GỬI PHIẾU ✉️", bg=BTN_PRIMARY, fg="white",
              font=("Segoe UI", 11, "bold"), width=15, relief="flat",
              activebackground=BTN_HOVER,
              command=submit_vote).pack(side="right", padx=10)
