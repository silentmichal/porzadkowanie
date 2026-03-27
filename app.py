import streamlit as st
import os
import pandas as pd
from logic.scanner import ImageScanner
from logic.processor import ImageProcessor

st.set_page_config(
    page_title="PhotoSort AI • Offline",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════
# PREMIUM CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ────────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    min-height: 100vh;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 2rem 2rem !important; }

/* ── Sidebar ─────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #13192a 0%, #0d1117 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.15) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }

/* ── Typography ──────────────────────────────────────────────── */
h1 { font-weight: 800 !important; letter-spacing: -1px; }
h2, h3 { font-weight: 700 !important; }

/* ── Buttons ─────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
    border: none !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.45) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(99,102,241,0.08) !important;
    color: #a5b4fc !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(99,102,241,0.15) !important;
    border-color: rgba(99,102,241,0.5) !important;
}

/* ── Inputs ──────────────────────────────────────────────────── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: white !important;
    font-size: 0.85rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

/* ── Tabs ────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
    font-size: 0.9rem;
    color: #94a3b8 !important;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: rgba(99,102,241,0.2) !important;
    color: #a5b4fc !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
}

/* ── Expander ────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    font-weight: 600 !important;
}

/* ── Slider ──────────────────────────────────────────────────── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #6366f1 !important;
}

/* ── DataFrame ───────────────────────────────────────────────── */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def metric_card(icon, label, value, color="#6366f1"):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(99,102,241,0.07), rgba(99,102,241,0.02));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 16px; padding: 20px 24px;
        display: flex; align-items: center; gap: 16px;">
        <div style="font-size: 2rem; line-height:1;">{icon}</div>
        <div>
            <div style="color:#64748b; font-size:0.75rem; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.08em;">{label}</div>
            <div style="color:white; font-size:1.6rem; font-weight:800;
                        line-height:1.2; margin-top:2px;">{value}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def photo_card(thumb_path, path, filename, date_taken, width, height, size_mb, camera):
    cam_short = (camera[:14] + "…") if len(str(camera)) > 14 else camera
    date_str  = date_taken if date_taken and date_taken != "None" else "—"
    try:
        b64 = ImageProcessor.get_base64_img(thumb_path if os.path.exists(thumb_path) else path)
        img_html = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;height:160px;object-fit:cover;border-radius:10px 10px 0 0;display:block;">'
    except:
        img_html = '<div style="height:160px;background:rgba(255,255,255,0.05);border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:center;color:#475569">🖼️</div>'

    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px; overflow: hidden;
        transition: all 0.25s ease; margin-bottom: 12px;">
        {img_html}
        <div style="padding: 10px 12px 12px;">
            <div style="color:white; font-size:0.78rem; font-weight:600;
                        overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
                        margin-bottom:6px;" title="{filename}">{filename}</div>
            <div style="display:flex; flex-direction:column; gap:3px;">
                <span style="color:#64748b; font-size:0.68rem;">📅 {date_str}</span>
                <span style="color:#64748b; font-size:0.68rem;">📏 {width}×{height} &nbsp;·&nbsp; 💾 {size_mb} MB</span>
                <span style="color:#64748b; font-size:0.68rem;">📷 {cam_short}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def open_folder_dialog():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        selected = filedialog.askdirectory(
            initialdir=st.session_state.folder,
            title="Wybierz folder ze zdjęciami"
        )
        root.destroy()
        if selected:
            st.session_state.folder = os.path.normpath(selected)
    except Exception as e:
        st.sidebar.warning(f"Dialog niedostępny: {e}")

def default_pictures():
    return os.path.join(os.path.expanduser("~"), "Pictures")

# ══════════════════════════════════════════════════════════════════
# STATE & SCANNER
# ══════════════════════════════════════════════════════════════════
BASE_DIR  = os.getcwd()
THUMB_DIR = os.path.join(BASE_DIR, ".thumbnails")
DB_PATH   = os.path.join(BASE_DIR, "photos.db")
os.makedirs(THUMB_DIR, exist_ok=True)

scanner = ImageScanner(DB_PATH)

if "folder" not in st.session_state:
    st.session_state.folder = default_pictures()

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo / Brand
    st.markdown("""
    <div style="text-align:center; padding: 0 0 20px 0;">
        <div style="font-size:2.5rem;">📷</div>
        <div style="font-size:1.1rem; font-weight:800; color:white; letter-spacing:-0.5px;">PhotoSort AI</div>
        <div style="font-size:0.72rem; color:#475569; margin-top:2px;">Offline • 100% prywatne</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#94a3b8; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em;">📂 Folder ze zdjęciami</p>', unsafe_allow_html=True)

    if st.button("🗂️ Przeglądaj…", use_container_width=True, type="secondary"):
        open_folder_dialog()

    # Quick shortcuts
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("🖼️", use_container_width=True, help="Moje Obrazy"):
            p = os.path.join(os.path.expanduser("~"), "Pictures")
            if os.path.isdir(p): st.session_state.folder = p
    with q2:
        if st.button("🖥️", use_container_width=True, help="Pulpit"):
            p = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.isdir(p): st.session_state.folder = p
    with q3:
        if st.button("📥", use_container_width=True, help="Pobrane"):
            p = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.isdir(p): st.session_state.folder = p

    folder_input = st.text_input("", value=st.session_state.folder, label_visibility="collapsed")
    if folder_input != st.session_state.folder:
        st.session_state.folder = folder_input

    folder_ok = os.path.isdir(st.session_state.folder)
    if folder_ok:
        st.markdown(f'<p style="color:#22c55e; font-size:0.75rem;">✅ Folder poprawny</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#ef4444; font-size:0.75rem;">❌ Folder nie istnieje</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    scan_btn = st.button("🚀 Skanuj teraz", use_container_width=True, type="primary", disabled=not folder_ok)

    st.markdown("---")

    # DB actions
    st.markdown('<p style="color:#94a3b8; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em;">🗄️ Baza danych</p>', unsafe_allow_html=True)
    df_count = scanner.get_all_images()
    st.markdown(f'<p style="color:#64748b; font-size:0.82rem;">Zaindeksowanych: <b style="color:#a5b4fc;">{len(df_count)}</b> zdjęć</p>', unsafe_allow_html=True)
    if st.button("🗑️ Wyczyść indeks", use_container_width=True, type="secondary"):
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM images")
        conn.commit()
        conn.close()
        st.rerun()

    st.markdown("---")
    st.markdown('<p style="color:#334155; font-size:0.72rem; text-align:center;">🔒 Dane nie opuszczają Twojego komputera</p>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
col_h, col_status = st.columns([3, 1])
with col_h:
    st.markdown("""
    <h1 style="color:white; margin-bottom:4px;">
        Porządkowanie Zdjęć <span style="
            background:linear-gradient(90deg,#6366f1,#a78bfa);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Offline</span>
    </h1>
    <p style="color:#475569; margin:0; font-size:0.95rem;">
        Automatyczne indeksowanie, tagowanie techniczne i wykrywanie duplikatów
    </p>
    """, unsafe_allow_html=True)
with col_status:
    st.markdown(f"""
    <div style="text-align:right; padding-top:12px;">
        <span style="background:rgba(34,197,94,0.1); color:#22c55e;
                     border:1px solid rgba(34,197,94,0.2); border-radius:20px;
                     padding:4px 12px; font-size:0.75rem; font-weight:600;">
            🟢 OFFLINE
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px;margin-bottom:24px;border-top:1px solid rgba(255,255,255,0.06);'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SKANOWANIE
# ══════════════════════════════════════════════════════════════════
if scan_btn:
    progress_bar = st.progress(0, text="Przygotowanie…")
    progress_bar.progress(20, text=f"🔍 Skanuję: {st.session_state.folder}")
    scanner.scan_directory(st.session_state.folder, THUMB_DIR)
    progress_bar.progress(100, text="✅ Gotowe!")
    import time; time.sleep(0.6)
    progress_bar.empty()
    st.toast("✅ Skanowanie zakończone!", icon="🚀")
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# DANE
# ══════════════════════════════════════════════════════════════════
df = scanner.get_all_images()

if df.empty:
    st.markdown("""
    <div style="
        background: rgba(99,102,241,0.05);
        border: 1px dashed rgba(99,102,241,0.25);
        border-radius: 20px; padding: 80px 20px; text-align:center; margin-top:40px;">
        <div style="font-size:4rem; margin-bottom:16px;">📁</div>
        <h3 style="color:#94a3b8; margin-bottom:8px;">Brak zaindeksowanych zdjęć</h3>
        <p style="color:#475569; max-width:400px; margin:0 auto;">
            Kliknij <b style="color:#a5b4fc;">🗂️ Przeglądaj…</b> w panelu bocznym,
            wybierz folder ze zdjęciami i naciśnij <b style="color:#a5b4fc;">🚀 Skanuj teraz</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["  📊 Statystyki  ", "  🖼️ Galeria  ", "  🔍 Podobne zdjęcia  "])

# ── TAB 1: STATYSTYKI ─────────────────────────────────────────────
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("🖼️", "Wszystkich zdjęć", len(df))
    with c2: metric_card("📁", "Folderów", df['folder'].nunique())
    total = df['file_size_mb'].sum()
    size_val = f"{round(total/1024,2)} GB" if total > 1024 else f"{round(total,1)} MB"
    with c3: metric_card("💾", "Łączny rozmiar", size_val)
    with c4: metric_card("📷", "Aparatów", df['camera_model'].nunique())

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<p style="color:#94a3b8; font-weight:600; font-size:0.9rem;">📁 Zdjęcia wg folderu</p>', unsafe_allow_html=True)
        folder_stats = df.groupby("folder").agg(
            Zdjęcia=("filename","count"),
            Rozmiar_MB=("file_size_mb","sum")
        ).reset_index().rename(columns={"folder":"Folder"})
        folder_stats["Rozmiar_MB"] = folder_stats["Rozmiar_MB"].round(1)
        st.dataframe(folder_stats, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown('<p style="color:#94a3b8; font-weight:600; font-size:0.9rem;">📷 Zdjęcia wg aparatu</p>', unsafe_allow_html=True)
        cam_stats = df.groupby("camera_model").size().reset_index(name="Zdjęcia").rename(columns={"camera_model":"Aparat"})
        st.dataframe(cam_stats, use_container_width=True, hide_index=True)

    # Timeline if dates available
    dated = df[df['date_taken'].notna() & (df['date_taken'] != 'None')]
    if not dated.empty:
        st.markdown('<br><p style="color:#94a3b8; font-weight:600; font-size:0.9rem;">📅 Zdjęcia wg roku</p>', unsafe_allow_html=True)
        dated = dated.copy()
        dated["rok"] = dated["date_taken"].str[:4]
        year_stats = dated.groupby("rok").size().reset_index(name="Liczba")
        st.bar_chart(year_stats.set_index("rok"), color="#6366f1")

# ── TAB 2: GALERIA ────────────────────────────────────────────────
with tab2:
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search = st.text_input("", placeholder="🔍  Szukaj po nazwie, folderze lub aparacie…", label_visibility="collapsed")
    with filter_col:
        sort_by = st.selectbox("", ["Najnowsze", "Nazwa A→Z", "Rozmiar ↓"], label_visibility="collapsed")

    filtered_df = df.copy()
    if search:
        mask = (
            df['filename'].str.contains(search, case=False, na=False) |
            df['folder'].str.contains(search, case=False, na=False) |
            df['camera_model'].str.contains(search, case=False, na=False)
        )
        filtered_df = df[mask].copy()

    if sort_by == "Nazwa A→Z":
        filtered_df = filtered_df.sort_values("filename")
    elif sort_by == "Rozmiar ↓":
        filtered_df = filtered_df.sort_values("file_size_mb", ascending=False)
    elif sort_by == "Najnowsze":
        filtered_df = filtered_df.sort_values("date_taken", ascending=False, na_position="last")

    st.markdown(f'<p style="color:#64748b; font-size:0.8rem; margin-bottom:12px;">Wyświetlam <b style="color:#a5b4fc;">{len(filtered_df)}</b> z <b>{len(df)}</b> zdjęć</p>', unsafe_allow_html=True)

    n_cols = 5
    cols = st.columns(n_cols)
    for idx, (_, row) in enumerate(filtered_df.iterrows()):
        with cols[idx % n_cols]:
            thumb_path = os.path.join(THUMB_DIR, f"thumb_{row['filename']}")
            photo_card(
                thumb_path, row['path'], row['filename'],
                row['date_taken'], row['width'], row['height'],
                row['file_size_mb'], row['camera_model']
            )

# ── TAB 3: PODOBNE ZDJĘCIA ────────────────────────────────────────
with tab3:
    st.markdown('<p style="color:#94a3b8; font-size:0.85rem;">Aplikacja porównuje odciski każdego zdjęcia — im mniejsza czułość, tym tylko bardziej identyczne zdjęcia są grupowane.</p>', unsafe_allow_html=True)

    threshold = st.slider("Próg podobieństwa", 0, 12, 5,
        help="0 = tylko identyczne kopie | 12 = luźno podobne")

    def hamming_dist(s1, s2):
        if not s1 or not s2 or len(s1) != len(s2): return 999
        return sum(c1 != c2 for c1, c2 in zip(s1, s2))

    with st.spinner("Szukam podobnych zdjęć…"):
        groups, visited = [], set()
        rows_list = list(df.iterrows())
        for i, (idx_i, row_i) in enumerate(rows_list):
            if idx_i in visited: continue
            group = [row_i]; visited.add(idx_i)
            for idx_j, row_j in rows_list[i+1:]:
                if idx_j in visited: continue
                if hamming_dist(row_i['phash'], row_j['phash']) <= threshold:
                    group.append(row_j); visited.add(idx_j)
            if len(group) > 1:
                groups.append(group)

    if not groups:
        st.markdown("""
        <div style="text-align:center; padding:60px; color:#475569;">
            <div style="font-size:3rem;">🎉</div>
            <p style="margin-top:12px;">Nie znaleziono podobnych zdjęć przy tej czułości.<br>
            Spróbuj zwiększyć próg podobieństwa.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        total_dupes = sum(len(g) - 1 for g in groups)
        st.markdown(f"""
        <div style="
            background: rgba(234,179,8,0.08); border: 1px solid rgba(234,179,8,0.2);
            border-radius: 12px; padding: 14px 20px; margin-bottom: 20px;
            display: flex; align-items: center; gap: 12px;">
            <span style="font-size:1.5rem;">⚠️</span>
            <span style="color:#fbbf24; font-weight:600;">
                Znaleziono <b>{len(groups)}</b> grup podobieństwa
                (około <b>{total_dupes}</b> potencjalnych duplikatów)
            </span>
        </div>
        """, unsafe_allow_html=True)

        for i, group in enumerate(groups):
            with st.expander(f"Grupa {i+1}  •  {len(group)} podobnych zdjęć"):
                gcols = st.columns(min(len(group), 5))
                for j, item in enumerate(group):
                    with gcols[j % 5]:
                        thumb_path = os.path.join(THUMB_DIR, f"thumb_{item['filename']}")
                        photo_card(
                            thumb_path, item['path'], item['filename'],
                            item['date_taken'], item['width'], item['height'],
                            item['file_size_mb'], item['camera_model']
                        )
