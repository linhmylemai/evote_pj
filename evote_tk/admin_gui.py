import tkinter as tk
from tkinter import ttk
from adapters import decrypt_vote, ensure_keys
import json, os, collections
import matplotlib.pyplot as plt

# ========== MÀU GIAO DIỆN ==========
BG_MAIN = "#f8f5ee"      # Kem
BG_SIDEBAR = "#3f3f46"   # Xám nâu
TXT_DARK = "#3f3f46"
TXT_LIGHT = "#f1f1f1"
BTN_PRIMARY = "#b5838d"  # Pastel hồng nâu

# ========== XỬ LÝ DỮ LIỆU ==========
def load_encrypted_votes():
    path = os.path.join("data", "votes_encrypted.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def tally_votes():
    ensure_keys()
    votes_enc = load_encrypted_votes()
    results_by_pos = collections.defaultdict(collections.Counter)
    for enc in votes_enc:
        try:
            plain = decrypt_vote(enc)
            pos = plain.get("position", "General")
            choice = plain.get("choice", "Unknown")
            results_by_pos[pos][choice] += 1
        except Exception as e:
            print("Decrypt error:", e)
    return results_by_pos

def show_bar_chart(results_by_pos):
    for pos, counter in results_by_pos.items():
        labels = list(counter.keys())
        values = list(counter.values())
        plt.figure(figsize=(5, 2.5))
        plt.barh(labels, values, color=BTN_PRIMARY)
        plt.title(f"{pos}")
        plt.xlabel("Votes")
        plt.tight_layout()
    plt.show()

# ========== GIAO DIỆN ADMIN ==========
def open_admin_window(parent):
    ensure_keys()

    # --- TẠO CỬA SỔ ---
    win = tk.Toplevel(parent)
    win.title("eVote Dashboard — Admin")
    win.geometry("1200x700")
    win.configure(bg=BG_MAIN)

    # --- SIDEBAR ---
    sidebar = tk.Frame(win, bg=BG_SIDEBAR, width=220)
    sidebar.pack(side="left", fill="y")

    tk.Label(sidebar, text="🗳 Online Voting", fg=TXT_LIGHT, bg=BG_SIDEBAR,
             font=("Segoe UI", 15, "bold")).pack(pady=(25, 15))

    sections = {
        "REPORTS": [("Dashboard", "dashboard"), ("Votes", "votes")],
        "MANAGE": [("Voters", "voters"), ("Positions", "positions"), ("Candidates", "candidates")],
        "SETTINGS": [("Ballot Position", "ballot"), ("Election Title", "election")]
    }

    # --- FRAME CHÍNH ---
    content = tk.Frame(win, bg=BG_MAIN)
    content.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    current_page = tk.StringVar(value="dashboard")

    # --- TRANG DASHBOARD ---
    def render_dashboard(frame):
        tk.Label(frame, text="📋 DASHBOARD", font=("Segoe UI", 18, "bold"),
                 bg=BG_MAIN, fg=TXT_DARK).pack(anchor="w", pady=(10, 20), padx=10)

        stats = [("No. of Positions", "4", "#a5b4fc"),
                 ("No. of Candidates", "9", "#fbbf24"),
                 ("Total Voters", "4", "#a78bfa"),
                 ("Voters Voted", "3", "#6ee7b7")]

        cards_frame = tk.Frame(frame, bg=BG_MAIN)
        cards_frame.pack(anchor="w", pady=(0, 20), padx=20)
        for i, (label, value, color) in enumerate(stats):
            frame_card = tk.Frame(cards_frame, bg=color, width=180, height=100)
            frame_card.grid(row=0, column=i, padx=15)
            frame_card.pack_propagate(False)
            tk.Label(frame_card, text=value, font=("Segoe UI", 20, "bold"), bg=color, fg="white").pack()
            tk.Label(frame_card, text=label, font=("Segoe UI", 10), bg=color, fg="white").pack()

        # --- BẢNG THỐNG KÊ ---
        tk.Label(frame, text="VOTES TALLY", bg=BG_MAIN, fg=TXT_DARK,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(10, 5))

        cols = ("Position", "Candidate", "Votes")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=250, anchor="center")
        tree.pack(fill="both", padx=20, pady=10, expand=True)

        def refresh_data():
            for i in tree.get_children():
                tree.delete(i)
            results = tally_votes()
            for pos, counter in results.items():
                for cand, v in counter.items():
                    tree.insert("", "end", values=(pos, cand, v))

        def view_chart():
            results = tally_votes()
            show_bar_chart(results)

        btns = tk.Frame(frame, bg=BG_MAIN)
        btns.pack(anchor="e", padx=20, pady=10)

        tk.Button(btns, text="🔄 Refresh", bg=BTN_PRIMARY, fg="white",
                  font=("Segoe UI", 10, "bold"), command=refresh_data).pack(side="left", padx=5)
        tk.Button(btns, text="📊 Chart", bg="#3b82f6", fg="white",
                  font=("Segoe UI", 10, "bold"), command=view_chart).pack(side="left", padx=5)

        refresh_data()

    # --- HIỂN THỊ CÁC TRANG ---
    def show_page(page_name):
        for widget in content.winfo_children():
            widget.destroy()

        if page_name == "dashboard":
            render_dashboard(content)

        elif page_name == "voters":
            tk.Label(content, text="📋 VOTERS LIST", font=("Segoe UI", 16, "bold"),
                     bg=BG_MAIN, fg=TXT_DARK).pack(pady=30)
            tk.Label(content, text="Trang hiển thị danh sách cử tri đăng ký.",
                     bg=BG_MAIN, fg="#6b6b6b").pack()

        elif page_name == "candidates":
            tk.Label(content, text="👤 CANDIDATES LIST", font=("Segoe UI", 16, "bold"),
                     bg=BG_MAIN, fg=TXT_DARK).pack(pady=30)
            tk.Label(content, text="Trang hiển thị danh sách ứng viên.",
                     bg=BG_MAIN, fg="#6b6b6b").pack()

        elif page_name == "votes":
            tk.Label(content, text="📊 VOTES RESULT", font=("Segoe UI", 16, "bold"),
                     bg=BG_MAIN, fg=TXT_DARK).pack(pady=30)
            tk.Label(content, text="Trang hiển thị kết quả bầu cử chi tiết.",
                     bg=BG_MAIN, fg="#6b6b6b").pack()

        else:
            tk.Label(content, text=f"{page_name.upper()} page đang phát triển...",
                     font=("Segoe UI", 13), bg=BG_MAIN, fg="#888").pack(pady=50)

    # --- TẠO NÚT SIDEBAR ---
    def make_sidebar_button(name, page_name):
        btn = tk.Label(sidebar, text=f"  {name}", bg=BG_SIDEBAR, fg="white",
                       font=("Segoe UI", 11), padx=25, pady=6, anchor="w")
        btn.pack(fill="x", padx=10)

        def on_click(event=None):
            current_page.set(page_name)
            for w in sidebar.winfo_children():
                if isinstance(w, tk.Label) and "  " in w.cget("text"):
                    w.config(bg=BG_SIDEBAR)
            btn.config(bg="#57534e")
            show_page(page_name)

        btn.bind("<Button-1>", on_click)
        btn.bind("<Enter>", lambda e: btn.config(bg="#4b5563"))
        btn.bind("<Leave>", lambda e: btn.config(bg=BG_SIDEBAR if current_page.get() != page_name else "#57534e"))
        return btn

    # --- VẼ DANH MỤC SIDEBAR ---
    for section, items in sections.items():
        tk.Label(sidebar, text=section, bg=BG_SIDEBAR, fg="#bfbfbf",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 3))
        for name, page_name in items:
            make_sidebar_button(name, page_name)

    # Trang mặc định
    show_page("dashboard")
