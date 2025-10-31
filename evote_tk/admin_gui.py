import tkinter as tk
from tkinter import ttk, messagebox
import csv, os
from collections import Counter

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


# ======= MAIN ADMIN WINDOW =======
def open_admin_login(parent):
    win = tk.Toplevel(parent)
    win.title("Trang quản trị — eVote AES+RSA")
    win.geometry("1150x720")
    win.configure(bg=BG_MAIN)

    # ===== CONTENT AREA =====
    content = tk.Frame(win, bg=BG_MAIN)
    content.pack(side="right", fill="both", expand=True)

    # ===== SIDEBAR =====
    sidebar = tk.Frame(win, bg=BG_SIDEBAR, width=220)
    sidebar.pack(side="left", fill="y")

    tk.Label(sidebar, text="🗳 CRCE Admin", bg=BG_SIDEBAR, fg="white",
             font=("Segoe UI", 14, "bold")).pack(pady=(20, 10))
    tk.Label(sidebar, text="● Online", bg=BG_SIDEBAR, fg="#22c55e").pack()

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

    # ====== SIDEBAR SECTIONS ======
    tk.Label(sidebar, text="\nREPORTS", bg=BG_SIDEBAR, fg="#d1d5db", anchor="w").pack(fill="x", padx=10)
    add_nav("Dashboard", show_dashboard)
    add_nav("Votes", show_votes)

    tk.Label(sidebar, text="\nMANAGE", bg=BG_SIDEBAR, fg="#d1d5db", anchor="w").pack(fill="x", padx=10)
    add_nav("Voters", show_voters)
    add_nav("Positions", show_positions)
    add_nav("Candidates", show_candidates)

    tk.Label(sidebar, text="\nSETTINGS", bg=BG_SIDEBAR, fg="#d1d5db", anchor="w").pack(fill="x", padx=10)
    add_nav("Ballot Position", lambda f: messagebox.showinfo("Ballot", "Tính năng đang phát triển..."))
    add_nav("Election Title", lambda f: messagebox.showinfo("Election", "Cài đặt tiêu đề bầu cử"))

    show_dashboard(content)


# ======= DASHBOARD =======
def show_dashboard(frame):
    for w in frame.winfo_children():
        w.destroy()

    data = load_data()
    num_pos = len(data["positions"])
    num_cand = len(data["candidates"])
    num_voters = len(data["voters"])
    num_voted = len(set(r.get("Mã cử tri") for r in data["votes"] if r.get("Mã cử tri")))

    # ====== HEADER ======
    header = tk.Frame(frame, bg=BG_MAIN)
    header.pack(fill="x", pady=(20, 10))
    tk.Label(header, text="📊 DASHBOARD", font=("Segoe UI", 22, "bold"),
             bg=BG_MAIN, fg="#b5651d").pack()

    # ====== STAT CARDS ======
    cards = [
        (num_pos, "No. of Positions", "#93c5fd"),
        (num_cand, "No. of Candidates", "#fcd34d"),
        (num_voters, "Total Voters", "#a5b4fc"),
        (num_voted, "Voters Voted", "#86efac")
    ]

    stat_frame = tk.Frame(frame, bg=BG_MAIN)
    stat_frame.pack(pady=(10, 30))

    for i, (val, label, color) in enumerate(cards):
        card = tk.Frame(stat_frame, bg=color, width=220, height=100, highlightbackground="#e5e7eb", highlightthickness=1)
        card.grid(row=0, column=i, padx=20, pady=10)
        card.grid_propagate(False)

        tk.Label(card, text=str(val), font=("Segoe UI", 26, "bold"),
                 bg=color, fg="#111827").pack(pady=(10, 0))
        tk.Label(card, text=label, font=("Segoe UI", 11, "bold"),
                 bg=color, fg="#374151").pack(pady=(5, 10))

    # ====== VOTES TALLY TABLE ======
    tk.Label(frame, text="VOTES TALLY", font=("Segoe UI", 16, "bold"),
             bg=BG_MAIN, fg=TXT_DARK).pack(pady=(5, 5))

    table_frame = tk.Frame(frame, bg=BG_MAIN)
    table_frame.pack(fill="both", expand=True, padx=40, pady=10)

    votes = data["votes"]
    cands = data["candidates"]

    # Map ứng viên
    cand_map = {}
    for c in cands:
        cid = c.get("Mã ứng viên")
        name = c.get("Họ và tên", "")
        pos = c.get("Chức vụ", "Unknown")
        if cid:
            cand_map[cid] = (name, pos)

    # Đếm phiếu
    tally = {}
    for v in votes:
        if v.get("Hợp lệ", "").lower() == "true":
            cid = v.get("Mã ứng viên")
            if cid in cand_map:
                name, pos = cand_map[cid]
                tally.setdefault(pos, Counter())[name] += 1

    columns = ("Position", "Candidate", "Votes")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=200)

    for pos, counts in tally.items():
        for name, num in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            tree.insert("", "end", values=(pos, name, num))

    tree.pack(fill="both", expand=True)


# ======= VOTES (chi tiết phiếu bầu) =======
def show_votes(frame):
    for w in frame.winfo_children():
        w.destroy()

    data = load_data()
    votes = data["votes"]
    cands = data["candidates"]

    tk.Label(frame, text="📋 VOTES REPORT", bg=BG_MAIN,
             fg="#b5651d", font=("Segoe UI", 18, "bold")).pack(pady=15)

    if not votes:
        tk.Label(frame, text="Không có dữ liệu phiếu bầu!", bg=BG_MAIN, fg="red").pack()
        return

    cand_map = {}
    for c in cands:
        cid = c.get("Mã ứng viên")
        name = c.get("Họ và tên", "")
        pos = c.get("Chức vụ", "Unknown")
        if cid:
            cand_map[cid] = (name, pos)

    columns = ("Mã phiếu", "Mã cử tri", "Ứng viên", "Chức vụ", "Hợp lệ", "Thời điểm")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=150)

    for v in votes:
        cid = v.get("Mã ứng viên")
        name, pos = cand_map.get(cid, ("Unknown", "Unknown"))
        tree.insert("", "end", values=(
            v.get("Mã phiếu"),
            v.get("Mã cử tri"),
            name,
            pos,
            v.get("Hợp lệ"),
            v.get("Thời điểm bỏ phiếu")
        ))

    tree.pack(fill="both", expand=True, padx=20, pady=10)


# ======= VOTERS =======
def show_voters(frame):
    show_table(frame, "cu_tri.csv", "🧑‍🤝‍🧑 VOTERS LIST")


# ======= POSITIONS =======
def show_positions(frame):
    show_table(frame, "chuc_vu.csv", "🏛 POSITIONS LIST")


# ======= CANDIDATES =======
def show_candidates(frame):
    for w in frame.winfo_children():
        w.destroy()

    path = os.path.join(DATA_DIR, "ung_vien.csv")
    rows = read_csv(path)

    tk.Label(frame, text="🎓 CANDIDATES LIST", bg=BG_MAIN, fg="#b5651d",
             font=("Segoe UI", 18, "bold")).pack(pady=(15, 5))

    # ======= SEARCH BAR =======
    search_frame = tk.Frame(frame, bg=BG_MAIN)
    search_frame.pack(pady=(0, 5))
    tk.Label(search_frame, text="Tìm theo tên:", bg=BG_MAIN).pack(side="left", padx=(0, 5))
    search_entry = tk.Entry(search_frame, width=30)
    search_entry.pack(side="left", padx=5)
    
    def search():
        keyword = search_entry.get().lower()
        filtered = [r for r in rows if keyword in r.get("Họ và tên", "").lower()]
        refresh_table(filtered)
    
    def show_all():
        refresh_table(rows)
        search_entry.delete(0, tk.END)

    tk.Button(search_frame, text="🔍 Tìm", command=search, bg="#93c5fd",
              font=("Segoe UI", 10, "bold")).pack(side="left", padx=3)
    tk.Button(search_frame, text="Hiện tất cả", command=show_all,
              bg="#e5e7eb", font=("Segoe UI", 10, "bold")).pack(side="left", padx=3)

    # ======= TABLE =======
    columns = list(rows[0].keys()) if rows else ["Mã ứng viên", "Họ và tên", "Chức vụ"]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor="center")
    tree.pack(fill="both", expand=True, padx=20, pady=(10, 20))

    def refresh_table(data):
        for i in tree.get_children():
            tree.delete(i)
        for r in data:
            tree.insert("", "end", values=list(r.values()))

    refresh_table(rows)

    # ======= BUTTONS =======
    btn_frame = tk.Frame(frame, bg=BG_MAIN)
    btn_frame.pack(pady=10)

    def save_csv(data):
        if not data: return
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def add_candidate():
        win = tk.Toplevel(frame)
        win.title("Thêm ứng viên mới")
        win.geometry("300x200")
        win.configure(bg=BG_MAIN)

        tk.Label(win, text="Mã ứng viên:", bg=BG_MAIN).pack(pady=5)
        e_id = tk.Entry(win, width=25); e_id.pack()
        tk.Label(win, text="Họ và tên:", bg=BG_MAIN).pack(pady=5)
        e_name = tk.Entry(win, width=25); e_name.pack()
        tk.Label(win, text="Chức vụ:", bg=BG_MAIN).pack(pady=5)
        e_pos = tk.Entry(win, width=25); e_pos.pack()

        def save():
            new = {"Mã ứng viên": e_id.get(), "Họ và tên": e_name.get(), "Chức vụ": e_pos.get()}
            if not all(new.values()):
                messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đầy đủ thông tin!")
                return
            rows.append(new)
            save_csv(rows)
            refresh_table(rows)
            messagebox.showinfo("Thành công", "Đã thêm ứng viên mới!")
            win.destroy()

        tk.Button(win, text="Lưu", bg="#86efac", command=save).pack(pady=10)

    def edit_candidate():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn 1 ứng viên để sửa!")
            return
        item = tree.item(selected[0])
        data = dict(zip(columns, item["values"]))
        win = tk.Toplevel(frame)
        win.title("Sửa thông tin ứng viên")
        win.geometry("300x200")
        win.configure(bg=BG_MAIN)

        tk.Label(win, text="Mã ứng viên:", bg=BG_MAIN).pack(pady=5)
        e_id = tk.Entry(win, width=25); e_id.insert(0, data["Mã ứng viên"]); e_id.pack()
        tk.Label(win, text="Họ và tên:", bg=BG_MAIN).pack(pady=5)
        e_name = tk.Entry(win, width=25); e_name.insert(0, data["Họ và tên"]); e_name.pack()
        tk.Label(win, text="Chức vụ:", bg=BG_MAIN).pack(pady=5)
        e_pos = tk.Entry(win, width=25); e_pos.insert(0, data["Chức vụ"]); e_pos.pack()

        def save_edit():
            for r in rows:
                if r["Mã ứng viên"] == data["Mã ứng viên"]:
                    r.update({"Họ và tên": e_name.get(), "Chức vụ": e_pos.get()})
                    break
            save_csv(rows)
            refresh_table(rows)
            messagebox.showinfo("Cập nhật", "Đã lưu thay đổi!")
            win.destroy()

        tk.Button(win, text="Lưu thay đổi", bg="#fcd34d", command=save_edit).pack(pady=10)

    def delete_candidate():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn 1 ứng viên để xoá!")
            return
        item = tree.item(selected[0])
        data = dict(zip(columns, item["values"]))
        confirm = messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xoá {data['Họ và tên']}?")
        if confirm:
            rows[:] = [r for r in rows if r["Mã ứng viên"] != data["Mã ứng viên"]]
            save_csv(rows)
            refresh_table(rows)
            messagebox.showinfo("Đã xoá", "Ứng viên đã được xoá!")

    tk.Button(btn_frame, text="➕ New", bg="#86efac", font=("Segoe UI", 10, "bold"),
              command=add_candidate).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✏️ Edit", bg="#fcd34d", font=("Segoe UI", 10, "bold"),
              command=edit_candidate).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🗑 Delete", bg="#fca5a5", font=("Segoe UI", 10, "bold"),
              command=delete_candidate).pack(side="left", padx=5)
# ======= VOTERS =======
def show_voters(frame):
    for w in frame.winfo_children():
        w.destroy()

    path = os.path.join(DATA_DIR, "cu_tri.csv")
    rows = read_csv(path)

    tk.Label(frame, text="🧑‍🤝‍🧑 VOTERS LIST", bg=BG_MAIN, fg="#b5651d",
             font=("Segoe UI", 18, "bold")).pack(pady=15)

    if not rows:
        tk.Label(frame, text="Không có dữ liệu!", bg=BG_MAIN, fg="red").pack()
        return

    columns = list(rows[0].keys())
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=150)

    for r in rows:
        tree.insert("", "end", values=list(r.values()))

    tree.pack(fill="both", expand=True, padx=20, pady=10)


# ======= POSITIONS =======
def show_positions(frame):
    for w in frame.winfo_children():
        w.destroy()

    path = os.path.join(DATA_DIR, "chuc_vu.csv")
    rows = read_csv(path)

    tk.Label(frame, text="🏛 POSITIONS LIST", bg=BG_MAIN, fg="#b5651d",
             font=("Segoe UI", 18, "bold")).pack(pady=15)

    if not rows:
        tk.Label(frame, text="Không có dữ liệu!", bg=BG_MAIN, fg="red").pack()
        return

    columns = list(rows[0].keys())
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=150)

    for r in rows:
        tree.insert("", "end", values=list(r.values()))

    tree.pack(fill="both", expand=True, padx=20, pady=10)
