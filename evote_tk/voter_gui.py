import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, pathlib
from datetime import datetime

# ===== STYLE =====
BG_MAIN = "#fdf6f0"
BG_CARD = "#fffefb"
TXT_DARK = "#111827"
BTN_PRIMARY = "#2563eb"
BTN_GRAY = "#9ca3af"
BTN_HOVER = "#1d4ed8"
TITLE_COLOR = "#b5651d"

# ===== ĐƯỜNG DẪN CSV =====
BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "server" / "data" / "input"

# ===== Helper: đọc CSV =====
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

# ===== Helper: ghi CSV (append) =====
def append_csv(path, row, headers):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# ===== GIAO DIỆN BỎ PHIẾU =====
def open_voter_window(parent, voter_id):
    parent.withdraw()
    win = tk.Toplevel()
    win.title("🗳 Bỏ phiếu điện tử — eVote")
    win.geometry("1100x700")
    win.configure(bg=BG_MAIN)

    # ===== HEADER =====
    tk.Label(win, text="🗳 BỎ PHIẾU ĐIỆN TỬ",
             font=("Segoe UI", 22, "bold"), bg=BG_MAIN, fg=TITLE_COLOR).pack(pady=(20, 5))
    tk.Label(win, text=f"Xin chào, {voter_id}",
             font=("Segoe UI", 11), bg=BG_MAIN, fg=TXT_DARK).pack(pady=(0, 15))

    # ===== KHUNG CUỘN =====
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

    # ===== Cuộn chuột mượt =====
    def smooth_scroll(event):
        direction = -1 if event.delta > 0 else 1
        canvas.yview_scroll(direction, "units")
        return "break"
    canvas.bind_all("<MouseWheel>", smooth_scroll)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    # ===== ĐỌC DỮ LIỆU =====
    chuc_vu = read_csv(DATA_DIR / "chuc_vu.csv")
    ung_vien = read_csv(DATA_DIR / "ung_vien.csv")
    cuoc_bau = read_csv(DATA_DIR / "cuoc_bau.csv")

    ma_cuoc_bau = cuoc_bau[0]["Mã cuộc bầu"] if cuoc_bau else "CB001"

    # ===== MAP MÃ ỨNG VIÊN → TÊN =====
    name_map = {u["Mã ứng viên"]: u["Họ và tên"] for u in ung_vien if u.get("Mã ứng viên")}

    # ===== GOM NHÓM ỨNG VIÊN THEO CHỨC VỤ =====
    grouped = {}
    for row in chuc_vu:
        pos = row.get("Chức vụ", "").strip()
        uid = row.get("Mã ứng viên", "").strip()
        if pos and uid:
            grouped.setdefault(pos, []).append(uid)

    selections = {}
    pos_list = list(grouped.items())
    cols = 3

    grid_roles = tk.Frame(scroll_frame, bg=BG_MAIN)
    grid_roles.pack(fill="x", padx=20, pady=10)

    # ===== HÀM TẠO RADIO CANVAS TO =====
    def make_radio(frame, group_var, value):
        """Tạo nút chọn tròn lớn kiểu web"""
        circle = tk.Canvas(frame, width=28, height=28, bg=BG_CARD, highlightthickness=0, bd=0)
        circle.pack(side="left", padx=(8, 10), pady=2)
        outer = circle.create_oval(3, 3, 25, 25, outline="#2563eb", width=2)
        inner = circle.create_oval(8, 8, 20, 20, fill="", outline="")

        def update_state(*_):
            if group_var.get() == value:
                circle.itemconfig(inner, fill="#2563eb")
            else:
                circle.itemconfig(inner, fill="")

        def select(event=None):
            group_var.set(value)
            update_state()

        # hiệu ứng hover
        circle.bind("<Enter>", lambda e: circle.itemconfig(outer, width=3))
        circle.bind("<Leave>", lambda e: circle.itemconfig(outer, width=2))
        circle.bind("<Button-1>", select)
        group_var.trace_add("write", update_state)
        return circle

    # ===== HIỂN THỊ DANH SÁCH CHỨC VỤ & ỨNG VIÊN =====
    for i, (pos, uvs) in enumerate(pos_list):
        role_card = tk.Frame(
            grid_roles,
            bg=BG_MAIN,
            bd=2,
            relief="groove",
            highlightbackground=TITLE_COLOR,
            highlightthickness=1
        )
        role_card.grid(row=i // cols, column=i % cols, padx=20, pady=15, sticky="n")

        tk.Label(role_card, text=pos.upper(),
                 font=("Segoe UI", 15, "bold"), bg=BG_MAIN, fg=TITLE_COLOR).pack(anchor="center", pady=(5, 10))

        var = tk.StringVar()
        selections[pos] = var

        tk.Label(role_card, text="Select only one candidate",
                 font=("Segoe UI", 10, "italic"), bg=BG_MAIN, fg="#6b7280").pack(anchor="center", pady=(0, 8))

        for uid in uvs:
            name = name_map.get(uid, f"Ứng viên {uid}")
            cand_card = tk.Frame(role_card, bg=BG_CARD, bd=1, relief="solid", padx=10, pady=8)
            cand_card.pack(fill="x", padx=10, pady=6)

            left = tk.Frame(cand_card, bg=BG_CARD)
            left.pack(fill="x")

            make_radio(left, var, uid)

            tk.Label(left, text=name, font=("Segoe UI", 13, "bold"),
                     bg=BG_CARD, fg=TXT_DARK).pack(side="left", padx=(0, 10))

            def show_info(uid=uid, pos=pos):
                info = next((u for u in ung_vien if u.get("Mã ứng viên") == uid), None)
                if not info:
                    messagebox.showwarning("Không tìm thấy", f"Không tìm thấy thông tin cho {uid}")
                    return
                ho_ten = info.get("Họ và tên", "Không rõ")
                msg = (
                    f"Ứng viên: {ho_ten}\n"
                    f"Ứng cử vị trí: {pos}\n"
                    f"Ghi chú: (Chưa có thêm thông tin chi tiết)"
                )
                messagebox.showinfo("Thông tin ứng viên", msg)

            tk.Button(left, text="Thông tin", bg=BTN_PRIMARY, fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat",
                      activebackground=BTN_HOVER, cursor="hand2",
                      command=lambda u=uid, p=pos: show_info(u, p)).pack(side="right")

    # ===== NÚT DƯỚI =====
    bottom = tk.Frame(win, bg=BG_MAIN)
    bottom.pack(fill="x", pady=15)

    def submit_vote():
        result = {pos: var.get() for pos, var in selections.items()}
        if any(v == "" for v in result.values()):
            messagebox.showwarning("Thiếu lựa chọn", "Vui lòng chọn ứng viên cho tất cả chức vụ!")
            return

        summary_text = "🗳 XÁC NHẬN PHIẾU BẦU\n\n"
        for pos, uid in result.items():
            name = name_map.get(uid, "Không rõ")
            summary_text += f"• {pos}: {name}\n"

        confirm = messagebox.askyesno(
            "Xác nhận bỏ phiếu",
            summary_text + "\n\nBạn có chắc muốn gửi phiếu bầu này không?"
        )
        if not confirm:
            messagebox.showinfo("Đã hủy", "Bạn có thể xem lại lựa chọn của mình trước khi gửi.")
            return

        phieu_raw_path = DATA_DIR / "phieu_bau_raw.csv"
        phieu_sach_path = DATA_DIR / "phieu_bau_sach.csv"

        existing = read_csv(phieu_raw_path)
        next_id = len(existing) + 1
        ma_phieu_base = f"PB{next_id:03d}"
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

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

        messagebox.showinfo("Gửi phiếu thành công ✅", "Phiếu của bạn đã được ghi nhận vào hệ thống!")
        win.destroy()
        parent.deiconify()

    tk.Button(bottom, text="ĐÓNG", bg=BTN_GRAY, fg="white",
              font=("Segoe UI", 11, "bold"), width=10, relief="flat",
              command=lambda: (win.destroy(), parent.deiconify())).pack(side="right", padx=10)

    tk.Button(bottom, text="GỬI PHIẾU ✉️", bg=BTN_PRIMARY, fg="white",
              font=("Segoe UI", 11, "bold"), width=15, relief="flat",
              activebackground=BTN_HOVER,
              command=submit_vote).pack(side="right", padx=10)
