import pathlib
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import csv, os
from collections import Counter

from matplotlib import style

# ⚙️ Ngăn Tkinter tự tạo root khi import
_root = tk.Tk()
_root.withdraw()
# Cấu hình font mặc định cho toàn bộ Treeview
style = ttk.Style()
style.configure("Treeview", font=("Segoe UI", 10))
style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))

# ======= STYLE =======
BG_MAIN = "#fdf6f0"
BG_SIDEBAR = "#3f3f46"
BG_CARD = "#f4ede4"
TXT_DARK = "#111827"
BTN_ACTIVE = "#b5651d"

DATA_DIR = os.path.join("..", "server", "data", "input")

# ======= Helper đọc CSV =======
def read_csv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for enc in ("utf-8-sig", "cp1258", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    break
        except Exception:
            pass
    return rows

# ======= Load data =======
def load_data():
    data = {}
    data["positions"] = read_csv(os.path.join(DATA_DIR, "chuc_vu.csv"))
    data["candidates"] = read_csv(os.path.join(DATA_DIR, "ung_vien.csv"))
    data["voters"] = read_csv(os.path.join(DATA_DIR, "cu_tri.csv"))
    data["votes"] = read_csv(os.path.join(DATA_DIR, "phieu_bau_sach.csv"))
    return data

def open_admin_login(parent):
    # Ẩn cửa sổ chính để tránh khung trắng
    parent.withdraw()

    win = tk.Toplevel(parent)
    win.title("Trang quản trị — eVote AES+RSA")
    win.geometry("1150x720")
    win.configure(bg=BG_MAIN)

    # Khi đóng cửa sổ admin → hiện lại cửa sổ chính
    def on_close():
        win.destroy()
        parent.deiconify()
    win.protocol("WM_DELETE_WINDOW", on_close)

    # ===== CONTENT AREA =====
    content = tk.Frame(win, bg=BG_MAIN)
    content.pack(side="right", fill="both", expand=True)

    # ===== SIDEBAR =====
    sidebar = tk.Frame(win, bg=BG_SIDEBAR, width=220)
    sidebar.pack(side="left", fill="y")

    # ===== HEADER SIDEBAR (Admin + Thoát) =====
    header_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
    header_frame.pack(fill="x", pady=(15, 5))

    tk.Label(header_frame, text="🗳 CRCE Admin", bg=BG_SIDEBAR, fg="white",
             font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)
    tk.Label(header_frame, text="● Online", bg=BG_SIDEBAR, fg="#22c55e",
             font=("Segoe UI", 10)).pack(side="left", padx=(5, 0))

    def logout():
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn thoát trang quản trị không?"):
            win.destroy()
            parent.deiconify()

    tk.Button(header_frame, text="🚪 Thoát", bg="#ef4444", fg="white",
              activebackground="#dc2626", relief="flat",
              font=("Segoe UI", 10, "bold"), cursor="hand2",
              command=logout).pack(side="right", padx=10)

    # ===== MENU SECTIONS =====
    def nav_action(callback):
        for w in content.winfo_children():
            w.destroy()
        callback(content)

    def add_nav(title, callback):
        btn = tk.Button(sidebar, text=title, bg=BG_SIDEBAR, fg="white",
                        activebackground=BTN_ACTIVE, relief="flat",
                        anchor="w", padx=20, font=("Segoe UI", 11),
                        command=lambda: nav_action(callback))
        btn.pack(fill="x", pady=2)

    tk.Label(sidebar, text="\nREPORTS", bg=BG_SIDEBAR, fg="#d1d5db", anchor="w").pack(fill="x", padx=10)
    add_nav("Dashboard", show_dashboard)
    # add_nav("Votes", show_votes)

    tk.Label(sidebar, text="\nMANAGE", bg=BG_SIDEBAR, fg="#d1d5db", anchor="w").pack(fill="x", padx=10)
    add_nav("Voters", show_voters)
    add_nav("Positions", show_positions)
    add_nav("Candidates", show_candidates)

    tk.Label(sidebar, text="\nSETTINGS", bg=BG_SIDEBAR, fg="#d1d5db", anchor="w").pack(fill="x", padx=10)
    add_nav("Ballot Position", lambda f: messagebox.showinfo("Ballot", "Tính năng đang phát triển..."))
    add_nav("Election Title", lambda f: messagebox.showinfo("Election", "Cài đặt tiêu đề bầu cử"))

    # Hiển thị mặc định dashboard
    show_dashboard(content)

def show_dashboard(frame):
    import os, csv, traceback
    import tkinter as tk
    from tkinter import ttk, messagebox, Toplevel, Frame, Label, Button
    from collections import defaultdict, Counter

    # ===== DỌN FRAME =====
    for w in frame.winfo_children():
        w.destroy()

    decrypt_done = False
    phieu = []
    path_chucvu = ""
    uv_map = {}
    # ===== ĐƯỜNG DẪN DỮ LIỆU =====
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(ROOT, "server", "data", "input")
    path_bau = os.path.join(DATA_DIR, "cuoc_bau.csv")
    path_phieu = os.path.join(DATA_DIR, "phieu_bau_sach.csv")
    path_uv = os.path.join(DATA_DIR, "ung_vien.csv")
    path_chucvu = os.path.join(DATA_DIR, "chuc_vu.csv")

    # ===== ĐỌC FILE =====
    def read_csv_safe(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                return list(csv.DictReader(f))
        return []

    cuoc_bau = read_csv_safe(path_bau)
    phieu = read_csv_safe(path_phieu)

    uv_map = {r.get("Mã ứng viên", "").strip(): r.get("Họ và tên", "Không rõ")
              for r in read_csv_safe(path_uv)}

    # ===== GOM PHIẾU THEO MÃ PHIẾU (PBxxx) =====
    grouped = defaultdict(list)
    for r in phieu:
        pid = (r.get("Mã phiếu") or "").split("_")[0]
        if pid:
            grouped[pid].append(r)

    # ===== HEADER =====
    header = Frame(frame, bg="#fdf6f0")
    header.pack(fill="x", pady=(15, 5))
    Label(header, text="🗳️ BẢNG ĐIỀU KHIỂN QUẢN TRỊ",
          bg="#fdf6f0", fg="#b5651d", font=("Segoe UI", 22, "bold")).pack()

    if cuoc_bau:
        cb = cuoc_bau[0]
        info = f"📅 Cuộc bầu cử: {cb.get('Tiêu đề','?')}   ⏰ {cb.get('Thời gian bắt đầu','?')} → {cb.get('Thời gian kết thúc','?')}"
        Label(frame, text=info, bg="#fdf6f0", fg="#6b7280",
              font=("Segoe UI", 11, "italic")).pack(pady=(0, 15))

    # ===== DANH SÁCH PHIẾU =====
    Label(frame, text="📋 DANH SÁCH PHIẾU CỬ TRI", bg="#fdf6f0",
          fg="#111827", font=("Segoe UI", 14, "bold")).pack()
    table_frame = Frame(frame, bg="#fdf6f0")
    table_frame.pack(fill="both", expand=True, padx=20, pady=(5, 5))

    columns = ("stt", "pid", "voter", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
    for c in columns:
        tree.column(c, anchor="center", width=180)
    for name, text in zip(columns, ["STT", "Mã phiếu", "Mã cử tri", "Trạng thái"]):
        tree.heading(name, text=text)
    tree.pack(fill="both", expand=True)

    # ===== HIỂN THỊ DANH SÁCH =====
    for i, (pid, items) in enumerate(grouped.items(), 1):
        valid = [x for x in items if (x.get("Hợp lệ") or "").lower() == "true"]
        count = len(valid)
        status = "✅ Đã đủ 8" if count >= 8 else f"❌ Thiếu {8 - count}"
        voter = (items[0].get("Mã cử tri") or "Không rõ")
        tree.insert("", "end", values=(i, pid, voter, status))

    # ===== KHUNG CHI TIẾT =====
    frame_detail = ttk.LabelFrame(frame, text="📄 CHI TIẾT PHIẾU (DỮ LIỆU MÃ HÓA)", padding=5)
    frame_detail.pack(fill="both", expand=True, padx=20, pady=10)
    tree_ct = ttk.Treeview(frame_detail, columns=("pos", "cipher"), show="headings", height=8)
    tree_ct.heading("pos", text="Vị trí / Chức vụ")
    tree_ct.heading("cipher", text="Dữ liệu mã hoá")
    tree_ct.column("pos", width=250, anchor="center")
    tree_ct.column("cipher", width=400, anchor="w")
    tree_ct.pack(fill="both", expand=True)

    # ===== XỬ LÝ KHI CHỌN PHIẾU =====
    def on_select(event):
        for i in tree_ct.get_children():
            tree_ct.delete(i)

        sel = tree.selection()
        if not sel:
            return

        pid = tree.item(sel[0])["values"][1]
        if not pid:
            return

        rows = [r for r in phieu if (r.get("Mã phiếu") or "").split("_")[0] == pid]
        valid = [r for r in rows if (r.get("Hợp lệ") or "").lower() == "true"]

        uv_to_pos = {}
        if os.path.exists(path_chucvu):
            with open(path_chucvu, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    uv_code = (row.get("Mã ứng viên") or "").strip()
                    pos_name = (row.get("Chức vụ") or "").strip()
                    if uv_code:
                        uv_to_pos[uv_code] = pos_name or "Không rõ"

        for r in valid:
            uv = (r.get("Mã ứng viên") or "").strip()
            uv_name = uv_map.get(uv, "Không rõ")
            pos_name = uv_to_pos.get(uv, "Không rõ")
            cipher = f"🔐 {uv_name[:8]}..."
            tree_ct.insert("", "end", values=(pos_name, cipher))

    tree.bind("<<TreeviewSelect>>", on_select)

    # ===== BIẾN TOÀN CỤC =====
    decrypt_done = False
    tally_counter = Counter()

    # ===== GIẢI MÃ PHIẾU =====
    def decrypt_votes():
        nonlocal decrypt_done, tally_counter
        try:
            decrypted = [r for r in phieu if (r.get("Hợp lệ") or "").lower() == "true"]
            for r in decrypted:
                cid = r.get("Mã ứng viên")
                name = uv_map.get(cid, f"UV {cid}")
                tally_counter[name] += 1
            decrypt_done = True
            messagebox.showinfo("✅ Thành công",
                                f"Đã giải mã {len(decrypted)} phiếu bầu hợp lệ.\nBấm '🧮 Kiểm phiếu' để xem kết quả.")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Lỗi", f"Không thể giải mã phiếu!\nChi tiết: {e}")

    
    def tally_now():
        import csv
        from tkinter import Label, ttk, Frame, messagebox
        from collections import Counter

        nonlocal decrypt_done, phieu, path_chucvu, uv_map
        if not decrypt_done:
            messagebox.showwarning("⚠️ Cảnh báo", "Hãy giải mã phiếu trước khi kiểm phiếu!")
            return

    # XÓA TOÀN BỘ KHUNG CŨ TRONG FRAME
        for w in frame.winfo_children():
            w.destroy()

    # ===== ĐỌC FILE CHỨC VỤ =====
        pos_map = {}
        try:
            with open(path_chucvu, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pos = (row.get("Chức vụ") or "").strip()
                    cid = (row.get("Mã ứng viên") or "").strip()
                    if pos:
                        pos_map.setdefault(pos, []).append(cid)
        except Exception as e:
            messagebox.showerror("❌ Lỗi", f"Không đọc được file chức vụ:\n{e}")
            return
    # ====== GIAO DIỆN CHÍNH (TRONG FRAME ADMIN) ======
        Label(frame, text="🧮 KẾT QUẢ KIỂM PHIẾU", font=("Segoe UI", 22, "bold"),
            bg="#fdf6f0", fg="#b45309").pack(pady=(15, 5))

        Label(frame, text="Chọn chức vụ để xem kết quả:",
            font=("Segoe UI", 11, "bold"), bg="#fdf6f0", fg="#78350f").pack(pady=(5, 5))

        combo_pos = ttk.Combobox(frame, values=list(pos_map.keys()), state="readonly", width=35)
        combo_pos.pack(pady=(0, 15))
        if pos_map:
            combo_pos.current(0)

    # ===== KHUNG HIỂN THỊ KẾT QUẢ =====
        result_frame = Frame(frame, bg="#fefaf6", highlightbackground="#e5e7eb", highlightthickness=1)
        result_frame.pack(padx=20, pady=10, fill="both", expand=True)

        def show_result(event=None):
            for w in result_frame.winfo_children():
                w.destroy()

            selected_pos = combo_pos.get().strip()
            if not selected_pos:
                return

            Label(result_frame, text=f"📊 KẾT QUẢ CHỨC VỤ: {selected_pos}",
                font=("Segoe UI", 12, "bold"), bg="#fefaf6", fg="#92400e").pack(anchor="w", padx=15, pady=(10, 5))

            candidates = pos_map.get(selected_pos, [])
            if not candidates:
                Label(result_frame, text="(Không có ứng viên cho chức vụ này)",
                      font=("Segoe UI", 10), bg="#fefaf6", fg="gray").pack(anchor="w", padx=20)
                return
        # ===== ĐẾM PHIẾU =====
            counts = Counter()
            for r in phieu:
                cid = (r.get("Mã ứng viên") or "").strip()
                if cid in candidates and str(r.get("Hợp lệ")).lower() == "true":
                    counts[cid] += 1
        # ===== HIỂN THỊ TẤT CẢ ỨNG VIÊN =====
            for cid in candidates:
                name = uv_map.get(cid, cid)
                num = counts.get(cid, 0)
                Label(result_frame,
                    text=f"• {name} — {num} phiếu",
                    font=("Segoe UI", 11),
                    bg="#fefaf6",
                    fg="#1f2937").pack(anchor="w", padx=25, pady=2)

        combo_pos.bind("<<ComboboxSelected>>", show_result)

    # ===== NÚT QUAY LẠI DASHBOARD =====
        from functools import partial
        from admin.dashboard import show_dashboard
        import sys
        if "evote_tk.admin_gui" in sys.modules:
            from evote_tk.admin_gui import show_dashboard as reload_dash
        else:
            reload_dash = show_dashboard

        ttk.Button(frame, text="🔙 Quay lại bảng điều khiển", command=lambda: reload_dash(frame)).pack(pady=15)

    # ===== LÀM MỚI DỮ LIỆU =====
    def refresh_data():
        for w in frame.winfo_children():
            w.destroy()
        show_dashboard(frame)

    # ===== CÁC NÚT =====
    btns = Frame(frame, bg="#fdf6f0")
    btns.pack(pady=10)
    Button(btns, text="🔓 Giải mã phiếu", bg="#93c5fd", font=("Segoe UI", 11, "bold"),
           command=decrypt_votes, width=20).pack(side="left", padx=10)
    Button(btns, text="🧮 Kiểm phiếu", bg="#86efac", font=("Segoe UI", 11, "bold"),
           command=tally_now, width=20).pack(side="left", padx=10)
    Button(btns, text="🔁 Làm mới dữ liệu", bg="#facc15", font=("Segoe UI", 11, "bold"),
           command=refresh_data, width=20).pack(side="left", padx=10)


# ======= VOTERS =======
def show_voters(frame):
    show_table(frame, "cu_tri.csv", "🧑‍🤝‍🧑 VOTERS LIST")


# ======= POSITIONS =======
def show_positions(frame):
    show_table(frame, "chuc_vu.csv", "🏛 POSITIONS LIST")


# ======= CANDIDATES =======
def show_candidates(frame):
    import pathlib, csv
    for w in frame.winfo_children():
        w.destroy()

    # ===== ĐƯỜNG DẪN CSV =====
    base_dir = pathlib.Path(__file__).resolve().parent
    path = base_dir.parent / "server" / "data" / "input" / "ung_vien.csv"
    path = path.resolve()

    # ===== HÀM ĐỌC & GHI CSV =====
    def read_candidates():
        rows = []
        if not path.exists():
            return rows
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "Mã ứng viên": (row.get("Mã ứng viên") or "").strip(),
                    "Họ và tên": (row.get("Họ và tên") or "").strip(),
                    "Chức vụ": (row.get("Chức vụ") or "").strip()
                })
        return rows

    def save_csv():
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Mã ứng viên", "Họ và tên", "Chức vụ"])
            writer.writeheader()
            writer.writerows(rows)

    rows = read_candidates()

    # ===== TIÊU ĐỀ =====
    tk.Label(frame, text="🎓 CANDIDATES LIST", bg=BG_MAIN, fg="#b5651d",
             font=("Segoe UI", 18, "bold")).pack(pady=(15, 5))

    # ===== THANH TÌM KIẾM =====
    search_frame = tk.Frame(frame, bg=BG_MAIN)
    search_frame.pack(pady=(5, 10))

    tk.Label(search_frame, text="🔍 Tìm theo tên:", bg=BG_MAIN, font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
    search_entry = tk.Entry(search_frame, width=30)
    search_entry.pack(side="left", padx=5)

    def refresh_table(data):
        for i in tree.get_children():
            tree.delete(i)
        for r in data:
            tree.insert("", "end", values=[r["Mã ứng viên"], r["Họ và tên"], r["Chức vụ"]])

    def search():
        keyword = search_entry.get().strip().lower()
        if not keyword:
            messagebox.showinfo("Thông báo", "Vui lòng nhập mã hoặc tên cần tìm!")
            return

        # 🔍 Tìm theo cả MÃ và TÊN
        filtered = [
            r for r in rows
            if keyword in r["Họ và tên"].lower() or keyword in r["Mã ứng viên"].lower()
        ]

        refresh_table(filtered)
        if not filtered:
            messagebox.showinfo("Kết quả", f"Không tìm thấy '{keyword}' trong danh sách.")


    def show_all():
        search_entry.delete(0, tk.END)
        refresh_table(rows)

    tk.Button(search_frame, text="🔍 Tìm", bg="#93c5fd", font=("Segoe UI", 10, "bold"),
              command=search).pack(side="left", padx=5)
    tk.Button(search_frame, text="📋 Hiện tất cả", bg="#e5e7eb", font=("Segoe UI", 10, "bold"),
              command=show_all).pack(side="left", padx=5)

    # ===== BẢNG DANH SÁCH =====
    table_frame = tk.Frame(frame, bg=BG_MAIN)
    table_frame.pack(fill="both", expand=True, padx=20, pady=(10, 5))

    columns = ["Mã ứng viên", "Họ và tên", "Chức vụ"]
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=230, anchor="center")

    scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scroll_y.set)
    scroll_y.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True, side="left")

    refresh_table(rows)

    # ===== HÀM PHỤ =====
    def next_candidate_id():
        max_id = 0
        for r in rows:
            code = r.get("Mã ứng viên", "").strip().replace("UV", "")
            if code.isdigit():
                max_id = max(max_id, int(code))
        return f"UV{max_id + 1:03d}"

    # ===== THÊM ỨNG VIÊN =====
    def add_candidate():
        win = tk.Toplevel(frame)
        win.title("Thêm ứng viên mới")
        win.geometry("300x220")
        win.configure(bg=BG_MAIN)
        win.resizable(False, False)

        new_id = next_candidate_id()

        tk.Label(win, text="Mã ứng viên:", bg=BG_MAIN).pack(pady=4)
        e_id = tk.Entry(win, width=25)
        e_id.insert(0, new_id)
        e_id.configure(state="readonly")
        e_id.pack()

        tk.Label(win, text="Họ và tên:", bg=BG_MAIN).pack(pady=4)
        e_name = tk.Entry(win, width=25)
        e_name.pack()

        tk.Label(win, text="Chức vụ:", bg=BG_MAIN).pack(pady=4)
        e_pos = tk.Entry(win, width=25)
        e_pos.pack()

        def save_new():
            name = e_name.get().strip()
            pos = e_pos.get().strip()
            if not name:
                messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập họ và tên!")
                return
            rows.append({"Mã ứng viên": new_id, "Họ và tên": name, "Chức vụ": pos})
            save_csv()
            refresh_table(rows)
            win.destroy()
            messagebox.showinfo("Thành công", f"Đã thêm ứng viên {name}!")

        tk.Button(win, text="Lưu", bg="#86efac", font=("Segoe UI", 10, "bold"),
                  command=save_new).pack(pady=10)

    # ===== CẬP NHẬT ỨNG VIÊN =====
    def update_candidate():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn ứng viên để sửa!")
            return
        cid, old_name, old_pos = tree.item(selected[0])["values"]

        win = tk.Toplevel(frame)
        win.title("Cập nhật ứng viên")
        win.geometry("300x220")
        win.configure(bg=BG_MAIN)
        win.resizable(False, False)

        tk.Label(win, text="Mã ứng viên:", bg=BG_MAIN).pack(pady=4)
        e_id = tk.Entry(win, width=25)
        e_id.insert(0, cid)
        e_id.configure(state="readonly")
        e_id.pack()

        tk.Label(win, text="Họ và tên:", bg=BG_MAIN).pack(pady=4)
        e_name = tk.Entry(win, width=25)
        e_name.insert(0, old_name)
        e_name.pack()

        tk.Label(win, text="Chức vụ:", bg=BG_MAIN).pack(pady=4)
        e_pos = tk.Entry(win, width=25)
        e_pos.insert(0, old_pos)
        e_pos.pack()

        def save_edit():
            new_name = e_name.get().strip()
            new_pos = e_pos.get().strip()
            if not new_name:
                messagebox.showwarning("Thiếu dữ liệu", "Tên không được để trống!")
                return
            for r in rows:
                if r["Mã ứng viên"] == cid:
                    r["Họ và tên"] = new_name
                    r["Chức vụ"] = new_pos
                    break
            save_csv()
            refresh_table(rows)
            win.destroy()
            messagebox.showinfo("Cập nhật", f"Đã lưu thay đổi cho {cid}!")

        tk.Button(win, text="Lưu thay đổi", bg="#fcd34d", font=("Segoe UI", 10, "bold"),
                  command=save_edit).pack(pady=10)

    # ===== XOÁ ỨNG VIÊN =====
    def delete_candidate():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn ứng viên để xoá!")
            return
        cid, name, _ = tree.item(selected[0])["values"]
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xoá {name}?"):
            rows[:] = [r for r in rows if r["Mã ứng viên"] != cid]
            save_csv()
            refresh_table(rows)
            messagebox.showinfo("Đã xoá", f"Đã xoá {name}!")

    # ===== NÚT HÀNH ĐỘNG =====
    btns = tk.Frame(frame, bg=BG_MAIN)
    btns.pack(pady=10)
    tk.Button(btns, text="➕ Thêm", bg="#86efac", font=("Segoe UI", 10, "bold"),
              command=add_candidate).pack(side="left", padx=5)
    tk.Button(btns, text="✏️ Sửa", bg="#fcd34d", font=("Segoe UI", 10, "bold"),
              command=update_candidate).pack(side="left", padx=5)
    tk.Button(btns, text="🗑 Xóa", bg="#fca5a5", font=("Segoe UI", 10, "bold"),
              command=delete_candidate).pack(side="left", padx=5)

# # ======= VOTERS =======
# def show_votes(frame):
#     import csv
#     for w in frame.winfo_children():
#         w.destroy()

#     path_votes = os.path.join(DATA_DIR, "phieu_bau_sach.csv")
#     path_cands = os.path.join(DATA_DIR, "ung_vien.csv")

#     votes = read_csv(path_votes)
#     candidates = read_csv(path_cands)

#     # ===== ÁNH XẠ ỨNG VIÊN =====
#     cand_map = {}
#     for c in candidates:
#         cid = c.get("Mã ứng viên")
#         if cid:
#             cand_map[cid] = (c.get("Họ và tên", ""), c.get("Chức vụ", ""))

#     tk.Label(frame, text="📋 VOTES REPORT", bg=BG_MAIN, fg="#b5651d",
#              font=("Segoe UI", 18, "bold")).pack(pady=(15, 5))

#     if not votes:
#         tk.Label(frame, text="Không có dữ liệu phiếu bầu!", bg=BG_MAIN, fg="red").pack()
#         return

#     # ===== THANH TÌM KIẾM =====
#     search_frame = tk.Frame(frame, bg=BG_MAIN)
#     search_frame.pack(pady=(5, 10))
#     tk.Label(search_frame, text="🔍 Tìm theo mã cử tri:", bg=BG_MAIN).pack(side="left", padx=(0, 5))
#     search_entry = tk.Entry(search_frame, width=30)
#     search_entry.pack(side="left", padx=5)

#     columns = ["Mã phiếu", "Mã cử tri", "Ứng viên", "Chức vụ", "Hợp lệ", "Thời điểm"]
#     tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
#     for col in columns:
#         tree.heading(col, text=col)
#         tree.column(col, anchor="center", width=150)

#     scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
#     tree.configure(yscroll=scroll_y.set)
#     scroll_y.pack(side="right", fill="y")
#     tree.pack(fill="both", expand=True, padx=20, pady=(10, 5))

#     def refresh_table(data):
#         for i in tree.get_children():
#             tree.delete(i)
#         for v in data:
#             cid = v.get("Mã ứng viên")
#             name, pos = cand_map.get(cid, ("Unknown", "Unknown"))
#             tree.insert("", "end", values=[
#                 v.get("Mã phiếu"), v.get("Mã cử tri"), name, pos,
#                 v.get("Hợp lệ"), v.get("Thời điểm bỏ phiếu")
#             ])

#     def search():
#         keyword = search_entry.get().strip().lower()
#         if not keyword:
#             messagebox.showinfo("Thông báo", "Vui lòng nhập mã cử tri cần tìm!")
#             return
#         filtered = [v for v in votes if keyword in (v.get("Mã cử tri") or "").lower()]
#         refresh_table(filtered)
#         if not filtered:
#             messagebox.showinfo("Kết quả", f"Không tìm thấy '{keyword}' trong danh sách phiếu.")

#     def show_all():
#         search_entry.delete(0, tk.END)
#         refresh_table(votes)

    # tk.Button(search_frame, text="🔍 Tìm", bg="#93c5fd", font=("Segoe UI", 10, "bold"),
    #           command=search).pack(side="left", padx=5)
    # tk.Button(search_frame, text="📋 Hiện tất cả", bg="#e5e7eb", font=("Segoe UI", 10, "bold"),
    #           command=show_all).pack(side="left", padx=5)

    # refresh_table(votes)



# ======= POSITIONS =======
def show_positions(frame):
    import csv, re
    for w in frame.winfo_children():
        w.destroy()

    path = os.path.join(DATA_DIR, "chuc_vu.csv")

    # ===== HÀM ĐỌC CSV & LÀM SẠCH =====
    def read_positions():
        rows = []
        if not os.path.exists(path):
            return rows
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
            content = f.read().replace("\ufeff", "").replace("\t", " ").strip()
        lines = [l for l in content.splitlines() if l.strip()]
        if not lines:
            return rows
        reader = csv.DictReader(lines)
        for row in reader:
            clean = {k.strip(): (v or "").strip() for k, v in row.items()}
            if "Tên chức vụ" not in clean:
                clean["Tên chức vụ"] = ""
            rows.append(clean)
        return rows

    def save_csv():
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Mã chức vụ", "Tên chức vụ"])
            writer.writeheader()
            writer.writerows(rows)

    rows = read_positions()

    # ===== GIAO DIỆN =====
    tk.Label(frame, text="🏛 POSITIONS LIST", bg=BG_MAIN, fg="#b5651d",
             font=("Segoe UI", 18, "bold")).pack(pady=(15, 5))

    if not rows:
        tk.Label(frame, text="Không có dữ liệu!", bg=BG_MAIN, fg="red").pack()
        return

    # ===== THANH TÌM KIẾM =====
    search_frame = tk.Frame(frame, bg=BG_MAIN)
    search_frame.pack(pady=(5, 10))
    tk.Label(search_frame, text="🔍 Tìm theo tên:", bg=BG_MAIN).pack(side="left", padx=(0, 5))
    search_entry = tk.Entry(search_frame, width=30)
    search_entry.pack(side="left", padx=5)

    def refresh_table(data):
        for i in tree.get_children():
            tree.delete(i)
        for r in data:
            tree.insert("", "end", values=[r["Mã chức vụ"], r["Tên chức vụ"]])

    def search():
        keyword = search_entry.get().strip().lower()
        if not keyword:
            messagebox.showinfo("Thông báo", "Vui lòng nhập tên chức vụ cần tìm!")
            return
        filtered = [r for r in rows if keyword in r["Tên chức vụ"].lower()]
        refresh_table(filtered)
        if not filtered:
            messagebox.showinfo("Kết quả", f"Không tìm thấy '{keyword}' trong danh sách.")

    def show_all():
        search_entry.delete(0, tk.END)
        refresh_table(rows)

    tk.Button(search_frame, text="🔍 Tìm", bg="#93c5fd", font=("Segoe UI", 10, "bold"),
              command=search).pack(side="left", padx=5)
    tk.Button(search_frame, text="📋 Hiện tất cả", bg="#e5e7eb", font=("Segoe UI", 10, "bold"),
              command=show_all).pack(side="left", padx=5)

    # ===== BẢNG =====
    table_frame = tk.Frame(frame, bg=BG_MAIN)
    table_frame.pack(fill="both", expand=True, padx=20, pady=(10, 5))

    columns = ["Mã chức vụ", "Tên chức vụ"]
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=250, anchor="center")

    scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scroll_y.set)
    scroll_y.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True, side="left")

    refresh_table(rows)

    # ===== CRUD =====
    def next_position_id():
        max_id = 0
        for r in rows:
            code = r.get("Mã chức vụ", "").strip().replace("CV", "")
            if code.isdigit():
                max_id = max(max_id, int(code))
        return f"CV{max_id + 1:03d}"

    def add_position():
        win = tk.Toplevel(frame)
        win.title("Thêm chức vụ")
        win.geometry("300x180")
        win.configure(bg=BG_MAIN)
        new_id = next_position_id()
        tk.Label(win, text="Mã chức vụ:", bg=BG_MAIN).pack()
        e_id = tk.Entry(win, width=25)
        e_id.insert(0, new_id)
        e_id.configure(state="readonly")
        e_id.pack()
        tk.Label(win, text="Tên chức vụ:", bg=BG_MAIN).pack()
        e_name = tk.Entry(win, width=25)
        e_name.pack()

        def save_new():
            name = e_name.get().strip()
            if not name:
                messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập tên chức vụ!")
                return
            rows.append({"Mã chức vụ": new_id, "Tên chức vụ": name})
            save_csv()
            refresh_table(rows)
            win.destroy()
            messagebox.showinfo("Thành công", f"Đã thêm chức vụ {name}!")

        tk.Button(win, text="Lưu", bg="#86efac", command=save_new).pack(pady=10)

    def update_position():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn chức vụ để sửa!")
            return
        cid, old_name = tree.item(selected[0])["values"]

        win = tk.Toplevel(frame)
        win.title("Cập nhật chức vụ")
        win.geometry("300x180")
        win.configure(bg=BG_MAIN)
        tk.Label(win, text="Mã chức vụ:", bg=BG_MAIN).pack()
        e_id = tk.Entry(win, width=25)
        e_id.insert(0, cid)
        e_id.configure(state="readonly")
        e_id.pack()
        tk.Label(win, text="Tên chức vụ:", bg=BG_MAIN).pack()
        e_name = tk.Entry(win, width=25)
        e_name.insert(0, old_name)
        e_name.pack()

        def save_edit():
            new_name = e_name.get().strip()
            if not new_name:
                messagebox.showwarning("Thiếu dữ liệu", "Tên không được trống!")
                return
            for r in rows:
                if r["Mã chức vụ"] == cid:
                    r["Tên chức vụ"] = new_name
                    break
            save_csv()
            refresh_table(rows)
            win.destroy()
            messagebox.showinfo("Cập nhật", f"Đã lưu thay đổi cho {cid}!")

        tk.Button(win, text="Lưu thay đổi", bg="#fcd34d", command=save_edit).pack(pady=10)

    def delete_position():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn chức vụ để xoá!")
            return
        cid, name = tree.item(selected[0])["values"]
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xoá {name}?"):
            rows[:] = [r for r in rows if r["Mã chức vụ"] != cid]
            save_csv()
            refresh_table(rows)
            messagebox.showinfo("Đã xoá", f"Đã xoá {name}!")

    btns = tk.Frame(frame, bg=BG_MAIN)
    btns.pack(pady=10)
    tk.Button(btns, text="➕ Thêm", bg="#86efac", command=add_position).pack(side="left", padx=5)
    tk.Button(btns, text="✏️ Sửa", bg="#fcd34d", command=update_position).pack(side="left", padx=5)
    tk.Button(btns, text="🗑 Xóa", bg="#fca5a5", command=delete_position).pack(side="left", padx=5)
