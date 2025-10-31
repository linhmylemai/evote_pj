# evote_tk/voter_gui.py
import os, csv, json, tkinter as tk
from tkinter import messagebox
from adapters import encrypt_vote, ensure_keys

# ======= MÀU CHỦ ĐẠO (pastel, giống web PHP) =======
BG = "#f7ecde"              # nền kem
BG_CARD = "#eee2cf"         # thẻ mục
BG_HEADER = "#d1ac7a"       # header nhẹ
TXT = "#2f2f2f"
BTN_BLUE = "#8ecae6"
BTN_GREEN = "#38a169"
BTN_GRAY = "#4b5563"
BORDER = "#c8b79e"

DATA_DIR = os.path.join("..", "server", "data", "input")
EVTK_DATA = os.path.join("evote_tk", "data")
VOTES_FILE = os.path.join(EVTK_DATA, "votes_encrypted.json")
BALLOT_STATE = os.path.join(EVTK_DATA, "ballots_status.json")  # lưu ai đã bỏ phiếu + lựa chọn

# ---------------------------------------------------
# Helpers đọc CSV “chịu lỗi header/encoding”
# ---------------------------------------------------
def _read_csv_smart(path, want_dict=True):
    if not os.path.exists(path):
        return []
    last = []
    for enc in ("utf-8-sig", "cp1258", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                if want_dict:
                    # Đoán header
                    first = f.readline()
                    if "," not in first:
                        f.seek(0)
                    else:
                        f.seek(0)
                    reader = csv.DictReader(f)
                    rows = list(reader)
                else:
                    reader = csv.reader(f)
                    rows = list(reader)
                if rows:
                    last = rows
                    break
        except Exception:
            pass
    return last

def load_positions():
    # chuc_vu.csv: linh hoạt cột (Mã chức vụ, Tên chức vụ) hoặc (Chức vụ)
    path = os.path.join(DATA_DIR, "chuc_vu.csv")
    rows = _read_csv_smart(path, want_dict=True)
    names = []
    for r in rows:
        val = r.get("Tên chức vụ") or r.get("Chức vụ") or r.get("ten_chuc_vu") or r.get("name") or ""
        val = val.strip()
        if val:
            names.append(val)
    # fallback nếu file trống
    if not names:
        names = ["President", "Vice President", "Secretary", "Treasurer"]
    return names

def load_candidates_group_by_position():
    """
    ung_vien.csv có thể có:
      - Mã ứng viên, Họ và tên, Chức vụ
      - Hoặc chỉ 2 cột (Mã ứng viên, Họ và tên) => gom vào một nhóm 'Candidates'
    Trả về: dict {position: [ {code, name}, ... ]}
    """
    path = os.path.join(DATA_DIR, "ung_vien.csv")
    rows = _read_csv_smart(path, want_dict=True)
    groups = {}
    if not rows:
        return groups

    # xác định tên cột linh hoạt
    for r in rows:
        code = (r.get("Mã ứng viên") or r.get("ma_ung_vien") or r.get("code") or "").strip()
        name = (r.get("Họ và tên") or r.get("ho_va_ten") or r.get("name") or "").strip()
        pos  = (r.get("Chức vụ") or r.get("chuc_vu") or r.get("position") or "").strip()

        if not pos:
            pos = "Candidates"  # fallback

        if pos not in groups:
            groups[pos] = []
        if name:
            groups[pos].append({"code": code, "name": name})
    return groups

# ---------------------------------------------------
# Trạng thái đã bỏ phiếu
# ---------------------------------------------------
def load_ballot_state():
    if not os.path.exists(BALLOT_STATE):
        return {}
    try:
        with open(BALLOT_STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_ballot_state(state: dict):
    os.makedirs(EVTK_DATA, exist_ok=True)
    with open(BALLOT_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------
# Gửi phiếu: mã hóa & lưu + đánh dấu đã bỏ
# ---------------------------------------------------
def submit_encrypted_ballot(voter_name: str, selections: dict):
    ensure_keys()
    os.makedirs(EVTK_DATA, exist_ok=True)

    payload = {
        "voter": voter_name,
        "choices": selections,  # {"President": "Tên A", ...}
    }
    enc = encrypt_vote(payload)

    # ghi append từng dòng JSON
    with open(VOTES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(enc, ensure_ascii=False) + "\n")

    # cập nhật trạng thái đã bỏ phiếu
    state = load_ballot_state()
    state[voter_name] = {"submitted": True, "selections": selections}
    save_ballot_state(state)

# ---------------------------------------------------
# UI: Success banner giống web
# ---------------------------------------------------
def show_success_banner(parent, voter_name):
    win = tk.Toplevel(parent)
    win.title("Ballot Submitted — eVote AES+RSA")
    win.configure(bg=BG)
    win.geometry("820x320")
    win.resizable(False, False)

    tk.Label(
        win, text="FR. CRCE COUNCIL ELECTION", bg=BG, fg=TXT,
        font=("Segoe UI", 24, "bold")
    ).pack(pady=(20, 12))

    # banner xanh
    banner = tk.Frame(win, bg="#22c55e", highlightbackground="#16a34a", highlightthickness=1)
    banner.pack(fill="x", padx=28, pady=(4, 18))

    msg = tk.Label(
        banner, text="✔  Success!  Ballot Submitted",
        bg="#22c55e", fg="white", font=("Segoe UI", 14, "bold"), anchor="w"
    )
    msg.pack(padx=18, pady=12, fill="x")

    # gợi ý xem lại
    tk.Label(
        win, text="You have already voted for this election.", bg=BG, fg=TXT,
        font=("Segoe UI", 12)
    ).pack(pady=(0, 14))

    def open_view_ballot():
        state = load_ballot_state().get(voter_name, {})
        selections = state.get("selections", {})
        # popup hiển thị lại chọn
        pv = tk.Toplevel(win)
        pv.title("View Ballot")
        pv.configure(bg=BG)
        pv.geometry("520x360")
        tk.Label(pv, text="Your Selections", bg=BG, fg=TXT, font=("Segoe UI", 16, "bold")).pack(pady=12)
        body = tk.Frame(pv, bg=BG)
        body.pack(fill="x", padx=22, pady=6)
        if not selections:
            tk.Label(body, text="(No data)", bg=BG, fg=TXT).pack()
        else:
            for pos, cand in selections.items():
                row = tk.Frame(body, bg=BG)
                row.pack(fill="x", pady=4)
                tk.Label(row, text=f"{pos}:", bg=BG, fg=TXT, font=("Segoe UI", 11, "bold"), width=14, anchor="w").pack(side="left")
                tk.Label(row, text=cand, bg=BG, fg=TXT, font=("Segoe UI", 11)).pack(side="left")
        tk.Button(pv, text="Close", command=pv.destroy, bg=BTN_GRAY, fg="white", relief="flat", padx=16, pady=6).pack(pady=14)

    tk.Button(
        win, text="View Ballot", command=open_view_ballot,
        bg=BTN_BLUE, fg="white", relief="flat", padx=18, pady=8,
        font=("Segoe UI", 11, "bold")
    ).pack()

# ---------------------------------------------------
# UI: Bỏ phiếu theo chức vụ + Preview popup
# ---------------------------------------------------
def open_voter_window(parent, voter_name: str):
    # Kiểm tra đã bỏ phiếu?
    st = load_ballot_state()
    if st.get(voter_name, {}).get("submitted"):
        # Đã bỏ: show banner luôn
        show_success_banner(parent, voter_name)
        return

    # Dữ liệu
    groups = load_candidates_group_by_position()
    if not groups:
        messagebox.showwarning("Không có dữ liệu", "Không tìm thấy danh sách ứng viên trong ung_vien.csv")
        return

    # Cửa sổ
    win = tk.Toplevel(parent)
    win.title("Bỏ phiếu — eVote AES+RSA")
    win.configure(bg=BG)
    win.geometry("1060x720")
    win.minsize(980, 650)

    # Header
    header = tk.Frame(win, bg=BG)
    header.pack(fill="x", pady=(18, 6))
    tk.Label(
        header, text="FR. CRCE COUNCIL ELECTION",
        bg=BG, fg=TXT, font=("Segoe UI", 24, "bold")
    ).pack()
    tk.Label(
        header, text=f"Xin chào, {voter_name}", bg=BG, fg=TXT, font=("Segoe UI", 11)
    ).pack(pady=(2, 10))

    # Canvas scroll
    canvas = tk.Canvas(win, bg=BG, highlightthickness=0)
    scroll = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    holder = tk.Frame(canvas, bg=BG)

    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=holder, anchor="nw")

    def _on_cfg(_):
        canvas.configure(scrollregion=canvas.bbox("all"))
    holder.bind("<Configure>", _on_cfg)

    # selections: map position -> tk.StringVar
    selected_vars = {}

    # Vẽ từng chức vụ (giống web: box + reset)
    for pos_name, cands in groups.items():
        card = tk.Frame(holder, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=26, pady=12)

        # Title + Reset
        top = tk.Frame(card, bg=BG_CARD)
        top.pack(fill="x", padx=18, pady=(12, 0))
        tk.Label(top, text=pos_name, bg=BG_CARD, fg=TXT, font=("Segoe UI", 14, "bold")).pack(side="left")

        v = tk.StringVar()
        selected_vars[pos_name] = v

        def make_reset(var=v):
            return lambda: var.set("")
        tk.Button(
            top, text="↻ Reset", command=make_reset(),
            bg="#86efac", fg="#14532d", relief="flat", padx=10, pady=4,
            font=("Segoe UI", 9, "bold")
        ).pack(side="right")

        # Body: list ứng viên (không ảnh)
        body = tk.Frame(card, bg=BG_CARD)
        body.pack(fill="x", padx=18, pady=(8, 16))

        for cand in cands:
            row = tk.Frame(body, bg=BG_CARD)
            row.pack(fill="x", pady=8)
            tk.Radiobutton(
                row, text=cand["name"], variable=v, value=cand["name"],
                bg=BG_CARD, fg=TXT, selectcolor=BG_CARD,
                font=("Segoe UI", 12, "bold"), anchor="w", width=38
            ).pack(side="left")

            # Nút Platform (demo – nếu sau này có platform text có thể show popup)
            tk.Button(
                row, text="🔎 Platform", bg=BTN_BLUE, fg="white",
                relief="flat", padx=10, pady=4, font=("Segoe UI", 9, "bold"),
                command=lambda nm=cand["name"], p=pos_name: messagebox.showinfo("Platform", f"{nm} — {p}\n(Chưa có dữ liệu platform)")
            ).pack(side="left", padx=(8, 0))

    # Hàng nút Preview / Submit
    btn_row = tk.Frame(holder, bg=BG)
    btn_row.pack(fill="x", padx=26, pady=18)

    # ----- Preview -----
    def do_preview():
        # Thu thập lựa chọn
        selections = {pos: var.get() for pos, var in selected_vars.items()}
        # Tạo popup preview giống web
        pv = tk.Toplevel(win)
        pv.title("Vote Preview")
        pv.configure(bg=BG)
        pv.geometry("680x440")
        pv.resizable(False, False)

        box = tk.Frame(pv, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        box.pack(fill="both", expand=True, padx=20, pady=18)

        tk.Label(box, text="Vote Preview", bg=BG_CARD, fg=TXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=10)

        body = tk.Frame(box, bg=BG_CARD)
        body.pack(fill="x", padx=22, pady=10)

        # render từng dòng
        for pos in selected_vars.keys():
            row = tk.Frame(body, bg=BG_CARD)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=f"{pos} :", bg=BG_CARD, fg=TXT, font=("Segoe UI", 11, "bold"), width=16, anchor="w").pack(side="left")
            val = selections.get(pos) or "(Chưa chọn)"
            tk.Label(row, text=val, bg=BG_CARD, fg=TXT, font=("Segoe UI", 11)).pack(side="left")

        footer = tk.Frame(box, bg=BG_CARD)
        footer.pack(fill="x", padx=16, pady=14)
        def _close():
            pv.destroy()
        tk.Button(footer, text="✖ Close", command=_close, bg=BTN_GRAY, fg="white", relief="flat", padx=14, pady=6).pack(side="left")

        def _submit_from_preview():
            pv.destroy()
            do_submit()  # gọi submit chung
        tk.Button(footer, text="✔ Submit", command=_submit_from_preview, bg=BTN_GREEN, fg="white", relief="flat", padx=16, pady=8, font=("Segoe UI", 10, "bold")).pack(side="right")

    # ----- Submit -----
    def do_submit():
        selections = {pos: var.get() for pos, var in selected_vars.items()}
        # Kiểm tra còn mục nào chưa chọn?
        missing = [p for p, v in selections.items() if not v]
        if missing:
            if not messagebox.askyesno("Thiếu chọn", f"Bạn chưa chọn cho các mục:\n- " + "\n- ".join(missing) + "\n\nBạn vẫn muốn gửi phiếu?"):
                return

        try:
            submit_encrypted_ballot(voter_name, selections)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể gửi phiếu: {e}")
            return

        # Disable form (khóa lại)
        for child in holder.winfo_children():
            try:
                child.configure(state="disabled")
            except Exception:
                pass

        show_success_banner(win, voter_name)

    tk.Button(
        btn_row, text="📄  Preview", command=do_preview,
        bg="#86efac", fg="#14532d", relief="flat", padx=18, pady=10,
        font=("Segoe UI", 11, "bold")
    ).pack(side="left")

    tk.Button(
        btn_row, text="✔  Submit", command=do_submit,
        bg=BTN_GREEN, fg="white", relief="flat", padx=18, pady=10,
        font=("Segoe UI", 11, "bold")
    ).pack(side="right")
import tkinter as tk
from tkinter import messagebox
import csv, os, json
from adapters import encrypt_vote, ensure_keys

# ======= STYLE =======
BG_MAIN = "#fdf6f0"
BG_LOGIN = "#f9fafb"
TXT_COLOR = "#111827"
BTN_BLUE = "#2563eb"
BTN_BLUE_HOVER = "#1e40af"
BG_CARD = "#f4ede4"
TXT_DARK = "#3f3f46"

# ======= ĐỌC DỮ LIỆU =======
def load_accounts():
    path = os.path.join("..", "server", "data", "input", "tai_khoan.csv")
    accounts = {}
    if not os.path.exists(path): return accounts
    for enc in ("utf-8-sig", "cp1258", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                rows = list(csv.reader(f))
                if not rows: continue
                if "tên" in rows[0][0].lower() or "user" in rows[0][0].lower():
                    rows = rows[1:]
                for r in rows:
                    if len(r) >= 2: accounts[r[0].strip()] = r[1].strip()
                break
        except Exception: pass
    return accounts

def load_candidates():
    path = os.path.join("..", "server", "data", "input", "ung_vien.csv")
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)

# ======= GỬI PHIẾU =======
def submit_vote(selected, voter_name):
    if not selected.get():
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn ứng viên!")
        return
    ensure_keys()
    data = {"voter": voter_name, "choice": selected.get()}
    enc = encrypt_vote(data)
    path = os.path.join("evote_tk", "data", "votes_encrypted.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(enc, ensure_ascii=False) + "\n")
    messagebox.showinfo("Thành công", f"Đã ghi nhận phiếu bầu cho {selected.get()}!")

# ======= BỎ PHIẾU =======
def open_voter_window(parent, voter_name):
    win = tk.Toplevel(parent)
    win.title("🗳 Bỏ phiếu điện tử — eVote AES+RSA")
    win.geometry("900x600")
    win.configure(bg=BG_MAIN)
    tk.Label(win, text="🗳 BỎ PHIẾU ĐIỆN TỬ", font=("Segoe UI", 22, "bold"), bg=BG_MAIN, fg="#b5651d").pack(pady=30)
    tk.Label(win, text=f"Xin chào, {voter_name}", bg=BG_MAIN, fg=TXT_DARK).pack()

    selected = tk.StringVar()
    candidates = load_candidates()
    if not candidates:
        tk.Label(win, text="Không có dữ liệu ứng viên", fg="red", bg=BG_MAIN).pack()
        return

    container = tk.Frame(win, bg=BG_MAIN)
    container.pack(pady=20)
    for c in candidates:
        name = c.get("Họ và tên", "")
        code = c.get("Mã ứng viên", "")
        card = tk.Frame(container, bg=BG_CARD, bd=2, relief="groove")
        card.pack(fill="x", padx=60, pady=5)
        tk.Radiobutton(card, text=f"{name} ({code})", variable=selected, value=name,
                       bg=BG_CARD, font=("Segoe UI", 12, "bold"),
                       selectcolor=BG_CARD).pack(anchor="w", padx=20, pady=8)
    tk.Button(win, text="GỬI PHIẾU", bg=BTN_BLUE, fg="white",
              activebackground=BTN_BLUE_HOVER, font=("Segoe UI", 13, "bold"),
              relief="flat", command=lambda: submit_vote(selected, voter_name)).pack(pady=25)

# ======= LOGIN GIAO DIỆN =======
def open_voter_window(parent, voter_name):
    win = tk.Toplevel(parent)
    win.title("🗳 Bỏ phiếu điện tử — eVote AES+RSA")
    win.geometry("980x680")
    win.configure(bg=BG_MAIN)

    # ===== Header =====
    header = tk.Frame(win, bg=BG_MAIN)
    header.pack(fill="x", pady=(20, 10))
    tk.Label(
        header, text="🗳 BỎ PHIẾU ĐIỆN TỬ",
        font=("Segoe UI", 22, "bold"),
        bg=BG_MAIN, fg="#b5651d"
    ).pack()
    tk.Label(
        header, text=f"Xin chào, {voter_name}",
        bg=BG_MAIN, fg=TXT_DARK, font=("Segoe UI", 11)
    ).pack(pady=(4, 10))

    # ===== Canvas (scrollable area) =====
    canvas = tk.Canvas(win, bg=BG_MAIN, highlightthickness=0)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=BG_MAIN)

    scroll_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=30)
    scrollbar.pack(side="right", fill="y")

    # ===== Candidate grid =====
    candidates = load_candidates()
    if not candidates:
        tk.Label(scroll_frame, text="Không có dữ liệu ứng viên", fg="red", bg=BG_MAIN).pack()
        return

    selected = tk.StringVar()
    cols = 3
    for i, c in enumerate(candidates):
        name = c.get("Họ và tên", "")
        code = c.get("Mã ứng viên", "")

        card = tk.Frame(
            scroll_frame, bg=BG_CARD, bd=2, relief="groove",
            width=250, height=120
        )
        card.grid(row=i // cols, column=i % cols, padx=15, pady=15, sticky="nsew")
        scroll_frame.grid_columnconfigure(i % cols, weight=1)

        # Nội dung card
        tk.Label(card, text=name, font=("Segoe UI", 12, "bold"),
                 bg=BG_CARD, fg=TXT_DARK).pack(pady=(15, 4))
        tk.Label(card, text=f"ID: {code}",
                 bg=BG_CARD, fg="#6b7280", font=("Segoe UI", 10)).pack(pady=(0, 6))
        tk.Radiobutton(
            card, text="Chọn ứng viên này", variable=selected, value=name,
            bg=BG_CARD, font=("Segoe UI", 10), selectcolor=BG_CARD
        ).pack(pady=(4, 6))

    # ===== Button row (fixed at bottom) =====
    btn_frame = tk.Frame(win, bg=BG_MAIN)
    btn_frame.pack(fill="x", side="bottom", pady=20, padx=40)

    def handle_submit():
        if not selected.get():
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một ứng viên trước khi gửi phiếu!")
            return
        ensure_keys()
        data = {"voter": voter_name, "choice": selected.get()}
        enc = encrypt_vote(data)
        path = os.path.join("evote_tk", "data", "votes_encrypted.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(enc, ensure_ascii=False) + "\n")
        messagebox.showinfo("Thành công", f"Phiếu của bạn cho {selected.get()} đã được ghi nhận!")
        win.destroy()

    tk.Button(
        btn_frame, text="GỬI PHIẾU 📨",
        bg=BTN_BLUE, fg="white", activebackground=BTN_BLUE_HOVER,
        font=("Segoe UI", 13, "bold"), relief="flat", padx=18, pady=10,
        command=handle_submit
    ).pack(side="right")

    tk.Button(
        btn_frame, text="Đóng",
        bg="#e5e7eb", fg="#111827", font=("Segoe UI", 11),
        relief="flat", padx=14, pady=8, command=win.destroy
    ).pack(side="right", padx=(0, 12))
