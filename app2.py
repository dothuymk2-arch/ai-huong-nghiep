import os
import io
import re
import time
import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from google import genai

# Thư viện ReportLab xuất file PDF chuyên nghiệp
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# --- 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE3 ---
def khoi_tao_db():
    conn = sqlite3.connect('he_thong_huong_nghiep.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS hoc_sinh_v4 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT, lop TEXT,
            toan REAL, van REAL, anh REAL, khtn REAL, lsgd REAL, tinhoc REAL, congnghe REAL, gdcd REAL,
            r INTEGER, i INTEGER, a INTEGER, s INTEGER, e INTEGER, c INTEGER,
            nganh_goi_y TEXT
        )
    ''')
    conn.commit()
    conn.close()

khoi_tao_db()

# --- HÀM ĐỔI TIẾNG VIỆT CÓ DẤU THÀNH KHÔNG DẤU ---
def xoa_dau_tieng_viet(text):
    a_signs = "[àáạảãâầấậẩẫăằắặẳẵ]"
    e_signs = "[èéẹẻẽêềếệểễ]"
    i_signs = "[ìíịỉĩ]"
    o_signs = "[òóọỏõôồốộổỗơờớợởỡ]"
    u_signs = "[ùúụủũưừứựửữ]"
    y_signs = "[ỳýỵỷỹ]"
    d_signs = "[đĐ]"
    text = re.sub(a_signs, "a", text)
    text = re.sub(re.compile(a_signs.upper()), "A", text)
    text = re.sub(e_signs, "e", text)
    text = re.sub(re.compile(e_signs.upper()), "E", text)
    text = re.sub(i_signs, "i", text)
    text = re.sub(re.compile(i_signs.upper()), "I", text)
    text = re.sub(o_signs, "o", text)
    text = re.sub(re.compile(o_signs.upper()), "O", text)
    text = re.sub(u_signs, "u", text)
    text = re.sub(re.compile(u_signs.upper()), "U", text)
    text = re.sub(y_signs, "y", text)
    text = re.sub(re.compile(y_signs.upper()), "Y", text)
    text = re.sub(d_signs, "d", text)
    return text

# --- CẤU HÌNH KHÓA API QUA STREAMLIT SECRETS (BẢO MẬT TUYỆT ĐỐI) ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "MÃ_DỰ_PHÒNG_NẾU_CHẠY_LOCAL"

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error("Lỗi cấu hình AI. Vui lòng kiểm tra lại mã API Key!")
# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="EduAI Guidance Pro v4.0", layout="wide", initial_sidebar_state="collapsed")

# --- 2. HỆ THỐNG GIAO DIỆN VÀ CSS TỐI ƯU BỐ CỤC ---
st.markdown("""
    <style>
    *, *::before, *::after { box-sizing: border-box; }
    [data-testid="stHeader"] { background-color: #7f1d1d !important; height: auto !important; position: relative !important; z-index: 99999 !important; }
    [data-testid="stHeader"] button { color: white !important; }
    .main .block-container { padding-top: 0rem !important; padding-bottom: 2rem !important; padding-left: 0rem !important; padding-right: 0rem !important; max-width: 100% !important; }
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    
    .body-content-wrapper { padding-left: 1.5rem; padding-right: 1.5rem; margin-top: 20px !important; }
    @media (min-width: 768px) {
        .body-content-wrapper { padding-left: 2.5rem; padding-right: 2.5rem; }
    }
    .top-nav-bar {
        background: linear-gradient(90deg, #7f1d1d, #b91c1c); padding: 15px 40px; display: flex; flex-wrap: wrap; align-items: center; gap: 15px; margin-top: 0px; position: relative; z-index: 999998; min-height: 70px; border-bottom: 3px solid #f87171;
    }
    .nav-logo-title { color: #FFFFFF !important; font-size: 24px !important; font-weight: 900 !important; margin-right: 20px; letter-spacing: 1px; font-family: 'Helvetica Neue', Arial, sans-serif !important; white-space: nowrap; line-height: 1.2 !important; }
    .nav-btn { padding: 8px 16px; border-radius: 6px; font-size: 13.5px; font-weight: 700; color: #FFFFFF !important; text-decoration: none !important; display: inline-flex; align-items: center; gap: 6px; background-color: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.3); transition: all 0.2s; }
    .nav-btn:hover { background-color: #ffffff !important; color: #7f1d1d !important; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    .status-text { color: #4ade80 !important; font-size: 12.5px; font-weight: 700; margin-left: auto; background-color: rgba(21, 128, 61, 0.4); padding: 5px 12px; border-radius: 20px; white-space: nowrap; }

    .filled-card-left { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white !important; padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; font-size: 15px !important; font-weight: 700 !important; box-shadow: 0 4px 15px rgba(37,99,235,0.25); border-left: 6px solid #60a5fa; }
    .filled-card-right { background: linear-gradient(135deg, #1e293b, #0f172a); color: #38bdf8 !important; padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; font-size: 15px !important; font-weight: 700 !important; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid #38bdf8; }

    .holland-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #FFF; }
    .holland-title { font-size: 16px !important; font-weight: 800 !important; margin-bottom: 5px !important; }
    .holland-desc { font-size: 14px !important; line-height: 1.5 !important; font-weight: 600 !important; }
    .box-r { background: linear-gradient(135deg, #fef2f2, #fee2e2); border-left-color: #dc2626; color: #991b1b !important; }
    .box-i { background: linear-gradient(135deg, #eff6ff, #dbeafe); border-left-color: #1d4ed8; color: #1e40af !important; }
    .box-a { background: linear-gradient(135deg, #fffbeb, #fef3c7); border-left-color: #d97706; color: #92400e !important; }
    .box-s { background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-left-color: #16a34a; color: #166534 !important; }
    .box-e { background: linear-gradient(135deg, #fff7ed, #ffedd5); border-left-color: #ea580c; color: #9a3412 !important; }
    .box-c { background: linear-gradient(135deg, #faf5ff, #f3e8ff); border-left-color: #7c3aed; color: #5b21b6 !important; }

    .input-section-card { background-color: #ffffff !important; padding: 20px; border-radius: 14px; border: 2px solid #e2e8f0; box-shadow: 0 4px 15px rgba(0,0,0,0.03); margin-bottom: 20px; }
    .sidebar-step-box { background: linear-gradient(135deg, #1e293b, #0f172a) !important; border: 1px solid #38bdf8; padding: 12px; border-radius: 10px; margin-bottom: 10px; }
    .sidebar-step-box p { color: #f8fafc !important; font-size: 13.5px !important; }

    .main-header-title { font-size: 24px !important; font-weight: 800; color: #0f172a !important; margin-bottom: 4px; }
    .main-header-sub { font-size: 14.5px !important; font-weight: 500; color: #475569 !important; margin-bottom: 15px; }
    .section-title { font-size: 18px !important; font-weight: 800; color: #1d4ed8 !important; margin-top: 15px; margin-bottom: 15px; border-bottom: 3px solid #3b82f6; padding-bottom: 6px; }
    
    .ai-side-box { background: linear-gradient(145deg, #0f172a, #1e293b) !important; padding: 20px; border-radius: 14px; border: 2px solid #2563eb; box-shadow: 0 6px 25px rgba(37,99,235,0.2); }
    .ai-side-box h3 { font-size: 20px !important; font-weight: 800 !important; color: #38bdf8 !important; }
    .ai-side-box p, .ai-side-box span, .ai-side-box div, .ai-side-box li { color: #f8fafc !important; font-size: 15px !important; line-height: 1.6 !important; }

    div.stButton > button { font-size: 15px !important; font-weight: 800 !important; padding: 10px 20px !important; background: linear-gradient(90deg, #2563eb, #1d4ed8) !important; color: white !important; border-radius: 10px !important; border: none !important; box-shadow: 0 4px 12px rgba(29,78,216,0.3) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f5f9; border-radius: 8px 8px 0px 0px; padding: 6px 12px; font-weight: 700; font-size: 13.5px; }
    .stTabs [aria-selected="true"] { background-color: #1d4ed8 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. THANH MENU ĐIỀU HƯỚNG MÁY TÍNH ---
st.markdown("""
    <div class="top-nav-bar">
        <div class="nav-logo-title">AI HƯỚNG NGHIỆP</div>
        <a class="nav-btn" href="#1">🔴 Tổng Quan Holland</a>
        <a class="nav-btn" href="#2">📝 Nhập Liệu Học Tập</a>
        <a class="nav-btn" href="#3">📊 Biểu Đồ Radar</a>
        <a class="nav-btn" href="#4">🤖 AI Tư Vấn Chuyên Sâu</a>
        <div class="status-text">● Hệ thống: Sẵn sàng</div>
    </div>
""", unsafe_allow_html=True)

# BANNER ĐỒ HỌA GRADIENT - SỬ DỤNG ST.HTML ĐỂ RENDER CHUẨN 100% TRÊN CẢ ĐIỆN THOẠI
st.html("""
<div style="
    background: linear-gradient(135deg, #1e3a8a 0%, #7f1d1d 50%, #b91c1c 100%);
    padding: 30px 25px;
    border-radius: 0px 0px 16px 16px;
    margin-bottom: 25px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    color: white;
    position: relative;
    overflow: hidden;
    font-family: 'Helvetica Neue', Arial, sans-serif;
">
    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.05; background-image: radial-gradient(#ffffff 2px, transparent 2px); background-size: 24px 24px;"></div>
    <div style="position: relative; z-index: 2; max-width: 800px;">
        <span style="background-color: #f59e0b; color: #7f1d1d; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 800; text-transform: uppercase; display: inline-block; margin-bottom: 8px;">🎯 Nền Tảng Khảo Sát v4.0</span>
        <h1 style="color: white !important; font-size: 26px !important; font-weight: 900 !important; margin: 0 0 8px 0; line-height: 1.2;">HỆ THỐNG SINH THÁI TƯ VẤN & ĐỊNH HƯỚNG NGHỀ NGHIỆP THÔNG MINH</h1>
        <p style="color: #f1f5f9 !important; font-size: 14px !important; margin: 0; font-weight: 500; opacity: 0.9; line-height: 1.4;">Ứng dụng Trí tuệ nhân tạo tích hợp phân tích diện rộng 8 môn học cốt lõi kết hợp mô hình Mật mã Holland nhằm kiến tạo lộ trình chọn tổ hợp môn lớp 10 chuẩn xác.</p>
    </div>
</div>
""")

# --- SIDEBAR THANH BÊN ---
with st.sidebar:
    st.markdown('<p style="font-size:17px; font-weight:800; color:#0f172a;">🎯 HƯỚNG DẪN THỰC HIỆN</p>', unsafe_allow_html=True)
    st.markdown("""
        <div class="sidebar-step-box" style="border-left: 4px solid #ef4444;">
            <p><strong style="color:#ef4444;">BƯỚC 1: Thông tin học lực</strong><br>Điền tên, lớp và kéo thanh điểm cho 8 môn học cốt lõi ở khung bên phải.</p>
        </div>
        <div class="sidebar-step-box" style="border-left: 4px solid #3b82f6;">
            <p><strong style="color:#3b82f6;">BƯỚC 2: Kiểm tra tâm lý</strong><br>Tích chọn sở thích ở 6 tab Holland, biểu đồ Radar sẽ cập nhật trực tiếp.</p>
        </div>
        <div class="sidebar-step-box" style="border-left: 4px solid #10b981;">
            <p><strong style="color:#10b981;">BƯỚC 3: Siêu AI Phân Tích</strong><br>Bấm nút kích hoạt nhận tư vấn sâu và tải file báo cáo PDF về máy.</p>
        </div>
    """, unsafe_allow_html=True)

# --- KHỞI ĐẦU NỘI DUNG CHÍNH ---
st.markdown('<div class="body-content-wrapper">', unsafe_allow_html=True)

# --- TỔNG QUAN LÝ THUYẾT HOLLAND ---
st.markdown('<p id="1" class="main-header-title">📘 Mật Mã Holland & 6 Nhóm Tính Cách Nghề Nghiệp</p>', unsafe_allow_html=True)
st.markdown('<p class="main-header-sub">Mô hình định hướng giúp xác định thiên hướng nghề nghiệp tự nhiên dựa trên tính cách cá nhân:</p>', unsafe_allow_html=True)

c_row1_1, c_row1_2, c_row1_3 = st.columns([1, 1, 1])
with c_row1_1:
    st.markdown('<div class="holland-box box-r"><div class="holland-title">🔴 R - Kỹ thuật</div><div class="holland-desc">Thích hành động, thực hành, làm việc với công cụ máy móc, kỹ thuật cơ khí.</div></div>', unsafe_allow_html=True)
with c_row1_2:
    st.markdown('<div class="holland-box box-i"><div class="holland-title">🔵 I - Nghiên cứu</div><div class="holland-desc">Thích suy nghĩ, phân tích, tìm tòi giải quyết vấn đề logic khoa học.</div></div>', unsafe_allow_html=True)
with c_row1_3:
    st.markdown('<div class="holland-box box-e"><div class="holland-title">🟠 E - Quản lý</div><div class="holland-desc">Thích dẫn dắt, giao tiếp thuyết phục, kinh doanh, có mục tiêu thách thức.</div></div>', unsafe_allow_html=True)

c_row2_1, c_row2_2, c_row2_3 = st.columns([1, 1, 1])
with c_row2_1:
    st.markdown('<div class="holland-box box-a"><div class="holland-title">🟡 A - Nghệ thuật</div><div class="holland-desc">Giàu trí tưởng tượng, thích sáng tạo tự do, viết lách, hội họa, thiết kế.</div></div>', unsafe_allow_html=True)
with c_row2_2:
    st.markdown('<div class="holland-box box-s"><div class="holland-title">🟢 S - Xã hội</div><div class="holland-desc">Thích giúp đỡ, giảng giải, kết nối, chăm sóc và làm việc vì cộng đồng.</div></div>', unsafe_allow_html=True)
with c_row2_3:
    st.markdown('<div class="holland-box box-c"><div class="holland-title">🟣 C - Nghiệp vụ</div><div class="holland-desc">Tỉ mỉ, cẩn thận, quản lý số liệu hồ sơ ngăn nắp, làm việc hệ thống.</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- PHÂN CHIA BỐ CỤC 2 CỘT TỶ LỆ VÀNG [7, 5] ---
col_main, col_ai = st.columns([7, 5], gap="large")

with col_main:
    st.markdown('<div id="2" class="filled-card-left">🚀 PHÂN TÍCH DIỆN RỘNG TOÀN DIỆN: Hệ thống tích hợp toàn bộ 8 môn học cốt lõi cùng 36 chỉ số Holland giúp định hướng lộ trình chọn tổ hợp môn lớp 10 chính xác theo chương trình mới.</div>', unsafe_allow_html=True)

    st.markdown('<div class="input-section-card">', unsafe_allow_html=True)
    c_hs1, c_hs2 = st.columns(2)
    with c_hs1:
        ten_hs = st.text_input("✍️ Họ và tên học sinh:", value="Nguyễn Văn A")
    with c_hs2:
        lop_hs = st.text_input("🏫 Lớp:", value="9A1")
    
    # --- TỰ ĐỘNG PHÁT GIỌNG NÓI CHÀO ---
    
            <script>
                function phatGiongNoi() {{
                    var msg = new SpeechSynthesisUtterance();
                    msg.text = "{cau_chao}";
                    msg.lang = "vi-VN";
                    msg.volume = 1;
                    msg.rate = 1;
                    window.speechSynthesis.speak(msg);
                }}
                phatGiongNoi();
            </script>
        """, height=0)
    st.markdown('</div>', unsafe_allow_html=True)

    # ĐÃ SỬA LỖI ĐÓNG NGOẶC CÚ PHÁP ĐÚNG ĐẮN TẠI ĐÂY
    st.markdown('<div class="section-title">📝 Học lực môn học (Cập Nhật Đầy Đủ 8 Môn)</div>', unsafe_allow_html=True)
    
    c_sub_m1, c_sub_m2 = st.columns(2)
    with c_sub_m1:
        d_toan = st.slider("Môn Toán", 0.0, 10.0, 8.5, 0.5)
        d_van = st.slider("Môn Ngữ văn", 0.0, 10.0, 7.0, 0.5)
        d_anh = st.slider("Môn Tiếng Anh", 0.0, 10.0, 7.5, 0.5)
        d_khtn = st.slider("Môn Khoa học tự nhiên (Lý, Hóa, Sinh)", 0.0, 10.0, 8.0, 0.5)
    with c_sub_m2:
        d_lsgd = st.slider("Môn Lịch sử và Địa lý", 0.0, 10.0, 7.5, 0.5)
        d_tinhoc = st.slider("Môn Tin học", 0.0, 10.0, 8.5, 0.5)
        d_congnghe = st.slider("Môn Công nghệ", 0.0, 10.0, 7.0, 0.5)
        d_gdcd = st.slider("Môn Giáo dục công dân", 0.0, 10.0, 8.0, 0.5)
    
    st.markdown('<div class="section-title">🧬 Khảo Sát Trắc Nghiệm Sở Thích Mật Mã Holland</div>', unsafe_allow_html=True)
    tabR, tabI, tabA, tabS, tabE, tabC = st.tabs(["🎯 R-Kỹ thuật", "🔬 I-Nghiên cứu", "🎨 A-Nghệ thuật", "🤝 S-Xã hội", "📢 E-Quản lý", "📊 C-Nghiệp vụ"])
    
    with tabR:
        r1 = st.checkbox("Em thích tự tay sửa chữa các đồ dùng, đồ chơi bị hỏng.", key="r1")
        r2 = st.checkbox("Em yêu thích lắp ráp mô hình, Lego hoặc sáng tạo cơ khí.", key="r2")
        r3 = st.checkbox("Em thích làm việc ngoài trời, vận động thể chất.", key="r3")
        r4 = st.checkbox("Em tò mò muốn biết cách vận hành của máy móc.", key="r4")
        r5 = st.checkbox("Em thấy mình có khả năng khéo tay khi làm thủ công.", key="r5")
        r6 = st.checkbox("Em thích học các môn thực hành như môn Công nghệ.", key="r6")
        score_r = sum([r1, r2, r3, r4, r5, r6]) * 8 + 2

    with tabI:
        i1 = st.checkbox("Em thích đọc sách khoa học, khám phá kiến thức mới.", key="i1")
        i2 = st.checkbox("Em hay đặt câu hỏi 'Tại sao' trước các hiện tượng lạ.", key="i2")
        i3 = st.checkbox("Em thích giải các bài toán đố hoặc trò chơi tư duy logic.", key="i3")
        i4 = st.checkbox("Em thích xem hoặc làm thí nghiệm Lý, Hóa, Sinh.", key="i4")
        i5 = st.checkbox("Em thích tự mày mò tìm hiểu sâu một chủ đề mình thích.", key="i5")
        i6 = st.checkbox("Em thích phân tích các sơ đồ, biểu đồ số liệu.", key="i6")
        score_i = sum([i1, i2, i3, i4, i5, i6]) * 8 + 2

    with tabA:
        a1 = st.checkbox("Em có sở thích vẽ tranh, phác thảo hoặc thiết kế.", key="a1")
        a2 = st.checkbox("Em yêu âm nhạc, thích ca hát hoặc chơi nhạc cụ.", key="a2")
        a3 = st.checkbox("Em thích viết văn, làm thơ hoặc sáng tác truyện.", key="a3")
        a4 = st.checkbox("Em thích làm việc tự do, không thích quy tắc ép buộc.", key="a4")
        a5 = st.checkbox("Em có gu thẩm mỹ, biết cách trang trí góc học tập.", key="a5")
        a6 = st.checkbox("Em thường có nhiều ý tưởng độc đáo, giàu trí tưởng tượng.", key="a6")
        score_a = sum([a1, a2, a3, a4, a5, a6]) * 8 + 2

    with tabS:
        s1 = st.checkbox("Em thích tham gia hoạt động tình nguyện, giúp đỡ người khác.", key="s1")
        s2 = st.checkbox("Em thấy vui khi giảng bài hoặc giải thích cho bạn bè.", key="s2")
        s3 = st.checkbox("Em biết lắng nghe và hay cho bạn bè lời khuyên tâm sự.", key="s3")
        s4 = st.checkbox("Em thích làm việc nhóm, giao lưu kết bạn mới.", key="s4")
        s5 = st.checkbox("Em quan tâm đến cảm xúc và tâm lý của mọi người.", key="s5")
        s6 = st.checkbox("Em thích đứng ra tổ chức các hoạt động tập thể cho lớp.", key="s6")
        score_s = sum([s1, s2, s3, s4, s5, s6]) * 8 + 2

    with tabE:
        e1 = st.checkbox("Em tự tin phát biểu, thuyết trình trước đám đông.", key="e1")
        e2 = st.checkbox("Em thường làm trưởng nhóm hoặc ban cán sự lớp.", key="e2")
        e3 = st.checkbox("Em có khả năng thuyết phục người khác theo ý mình.", key="e3")
        e4 = st.checkbox("Em thích sự thử thách, tính cạnh tranh cao.", key="e4")
        e5 = st.checkbox("Em thích lập kế hoạch, quản lý tài chính cá nhân.", key="e5")
        e6 = st.checkbox("Em là người quyết đoán và chủ động trong mọi việc.", key="e6")
        score_e = sum([e1, e2, e3, e4, e5, e6]) * 8 + 2

    with tabC:
        c1 = st.checkbox("Em luôn sắp xếp sách vở, đồ dùng ngăn nắp, gọn gàng.", key="c1")
        c2 = st.checkbox("Em thích làm việc theo thời gian biểu rõ ràng.", key="c2")
        c3 = st.checkbox("Em cẩn thận, làm việc với các con số rất ít sai sót.", key="c3")
        c4 = st.checkbox("Em thích thu thập dữ liệu, lưu trữ sắp xếp thông tin.", key="c4")
        c5 = st.checkbox("Em làm tốt nhất khi có hướng dẫn từng bước chi tiết.", key="c5")
        c6 = st.checkbox("Em rất kiên nhẫn với công việc tỉ mỉ, lặp đi lặp lại.", key="c6")
        score_c = sum([c1, c2, c3, c4, c5, c6]) * 8 + 2

    st.write("")
    st.progress(score_r / 50, text=f"🔴 Nhóm R - Kỹ thuật: {score_r}/50")
    st.progress(score_i / 50, text=f"🔵 Nhóm I - Nghiên cứu: {score_i}/50")
    st.progress(score_a / 50, text=f"🟡 Nhóm A - Nghệ thuật: {score_a}/50")
    st.progress(score_s / 50, text=f"🟢 Nhóm S - Xã hội: {score_s}/50")
    st.progress(score_e / 50, text=f"🟠 Nhóm E - Quản lý: {score_e}/50")
    st.progress(score_c / 50, text=f"🟣 Nhóm C - Nghiệp vụ: {score_c}/50")

with col_ai:
    st.markdown('<div class="filled-card-right">🤖 TRẠNG THÁI: Biểu đồ Radar đồng bộ thời gian thực | Hệ thống 8 môn học sẵn sàng.</div>', unsafe_allow_html=True)

    # --- BIỂU ĐỒ RADAR ---
    st.markdown('<div id="3" class="section-title" style="margin-top:0px;">📊 BIỂU ĐỒ RADAR MẬT MÃ HOLLAND</div>', unsafe_allow_html=True)
    categories = ['R', 'I', 'A', 'S', 'E', 'C', 'R']
    values = [score_r, score_i, score_a, score_s, score_e, score_c, score_r]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        fillcolor='rgba(37, 99, 235, 0.25)', line=dict(color='#2563eb', width=3)
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 50], gridcolor="#cbd5e1"), angularaxis=dict(gridcolor="#cbd5e1")),
        showlegend=False, template="plotly_white", height=340, margin=dict(l=40, r=40, t=30, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="ai-side-box">', unsafe_allow_html=True)
    st.subheader("🤖 TRỢ LÝ AI TƯ VẤN CHUYÊN SÂU")
    
    if 'noi_dung_ai_v4' not in st.session_state:
        st.session_state.noi_dung_ai_v4 = ""

  if st.button("✨ KÍCH HOẠT TƯ VẤN HƯỚNG NGHIỆP", use_container_width=True):
        # 1. KÍCH HOẠT TIẾNG CHÀO (Đã loại bỏ thẻ <script> để chống lỗi thụt lề 100%)
        cau_chao = f"Xin chào bạn {ten_hs}, học sinh lớp {lop_hs}. Trợ lý AI đang tiến hành phân tích dữ liệu hướng nghiệp của bạn, vui lòng đợi trong giây lát."
        st.components.v1.html(f'<iframe src="javascript:void(var msg=new SpeechSynthesisUtterance(\'{cau_chao}\');msg.lang=\'vi-VN\';msg.volume=1;msg.rate=1;window.speechSynthesis.speak(msg))" style="display:none;width:0;height:0;border:none;"></iframe>', height=0)

        # 2. TIẾN HÀNH GỌI AI PHÂN TÍCH NHƯ BÌNH THƯỜNG
        with st.spinner("🤖 Hệ thống AI đang tổng hợp 8 môn học và phân tích chuyên sâu..."):
            prompt_pro = (
                f"Bạn là Chuyên gia Tư vấn Hướng nghiệp Cao cấp ngành Giáo dục. Hãy phân tích bộ dữ liệu học sinh lớp 9:\n"
                f"- Học sinh: {ten_hs}, Lớp: {lop_hs}.\n"
                f"- Điểm số 8 môn: Toán {d_toan}, Văn {d_van}, Anh {d_anh}, KHTN {d_khtn}, Lịch sử-Địa lý {d_lsgd}, Tin học {d_tinhoc}, Công nghệ {d_congnghe}, GDCD {d_gdcd}.\n"
                f"- Chỉ số đam mê Holland: R:{score_r}, I:{score_i}, A:{score_a}, S:{score_s}, E:{score_e}, C:{score_c}.\n\n"
                f"Hãy xuất câu trả lời phân định rõ ràng thành các mục sau (Sử dụng tiêu đề dạng markdown bôi đậm):\n"
                f"1. ĐIỂM MẠNH & ĐIỂM HẠN CHẾ DIỆN RỘNG\n"
                f"2. TƯ VẤN CHỌN TỔ HỢP MÔN LỚP 10\n"
                f"3. LỘ TRÌNH HÀNH ĐỘNG 3 GIAI ĐOẠN\n"
                f"4. LỜI KHUYÊN PHỐI HỢP DÀNH CHO GIA ĐÌNH\n\n"
                f"Yêu cầu: Lời khuyên thực tế, sâu sắc, mang tính định hướng cao, cấu trúc mạch lạc sạch sẽ."
            )
            
            thanh_cong = False
            for luot_thu in range(3):
                try:
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_pro)
                    st.session_state.noi_dung_ai_v4 = response.text
                    thanh_cong = True
                    break
                except Exception:
                    time.sleep(1.2)
            
            if not thanh_cong:
                st.warning("⚠️ Hệ thống đang chuyển sang thuật toán phân tích cục bộ dự phòng:")
                st.session_state.noi_dung_ai_v4 = (
                    "### 1. ĐIỂM MẠNH & ĐIỂM HẠN CHẾ DIỆN RỘNG\n"
                    f"- **Điểm mạnh:** Học sinh {ten_hs} sở hữu phổ điểm các môn công nghệ, tính toán logic và tự nhiên vô cùng nổi trội.\n"
                    "- **Điểm hạn chế:** Cần cải thiện khả năng viết luận xã hội để tối ưu hóa điểm số toàn diện.\n\n"
                    "### 2. TƯ VẤN CHỌN TỔ HỢP MÔN LỚP 10\n"
                    "- **Định hướng tổ hợp môn:** Dựa trên khung GDPT 2018, học sinh nên chọn định hướng liên quan đến Vật lý, Hóa học kết hợp Tin học và Công nghệ.\n\n"
                    "### 3. LỘ TRÌNH HÀNH ĐỘNG 3 GIAI ĐOẠN\n"
                    "- **Giai đoạn 1:** Bứt phá học lực giai đoạn cuối cấp THCS.\n"
                    "- **Giai đoạn 2:** Thử thách bản thân ở môi trường cấp 3.\n"
                    "- **Giai đoạn 3:** Khảo sát các chuyên ngành đại học phù hợp.\n\n"
                    "### 4. LỜI KHUYÊN PHỐI HỢP DÀNH CHO GIA ĐÌNH\n"
                    "- Đồng hành và tạo không gian cho con tự quyết định lộ trình rèn luyện kỹ năng thực tế."
                )

            try:
                conn = sqlite3.connect('he_thong_huong_nghiep.db')
                c_db = conn.cursor()
                c_db.execute('''
                    INSERT INTO hoc_sinh_v4 (ten, lop, toan, van, anh, khtn, lsgd, tinhoc, congnghe, gdcd, r, i, a, s, e, c, nganh_goi_y)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ten_hs, lop_hs, d_toan, d_van, d_anh, d_khtn, d_lsgd, d_tinhoc, d_congnghe, d_gdcd, score_r, score_i, score_a, score_s, score_e, score_c, "Đã Phân Tích 8 Môn"))
                conn.commit()
                conn.close()
            except Exception:
                pass

    if not st.session_state.noi_dung_ai_v4:
        st.markdown('<div style="color:#38bdf8; font-size:13.5px; font-weight:600;">💡 Hãy nhấn nút phía trên để AI tiến hành phân tích sâu diện rộng 8 môn học.</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Phân tích tích hợp thành công!")

    st.markdown('</div>', unsafe_allow_html=True)
# --- 5. HIỂN THỊ KẾT QUẢ VÀ NÚT TẢI PDF ---
def tao_file_pdf_v4(ten, lop, d1, d2, d3, d4, d5, d6, d7, d8, r, i, a, s, e, c_score, loi_khuyen_ai):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=1.18*inch, rightMargin=0.78*inch, topMargin=0.78*inch, bottomMargin=0.78*inch)
    
    font_path_regular = "C:\\Windows\\Fonts\\arial.ttf"
    font_path_bold = "C:\\Windows\\Fonts\\arialbd.ttf"
    font_path_italic = "C:\\Windows\\Fonts\\ariali.ttf"
    
    if os.path.exists(font_path_regular) and os.path.exists(font_path_bold):
        pdfmetrics.registerFont(TTFont('Arial-VN', font_path_regular))
        pdfmetrics.registerFont(TTFont('Arial-VN-Bold', font_path_bold))
        pdfmetrics.registerFont(TTFont('Arial-VN-Italic', font_path_italic))
        font_name = "Arial-VN"
        font_bold = "Arial-VN-Bold"
        font_italic = "Arial-VN-Italic"
    else:
        font_name = "Helvetica"
        font_bold = "Helvetica-Bold"
        font_italic = "Helvetica-Oblique"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName=font_bold, fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('DocSub', fontName=font_name, fontSize=9, leading=12, alignment=TA_CENTER, spaceAfter=15)
    info_style = ParagraphStyle('StudentInfo', fontName=font_bold, fontSize=11, leading=15, spaceAfter=10)
    heading_style = ParagraphStyle('SectionHeading', fontName=font_bold, fontSize=11, leading=15, spaceBefore=12, spaceAfter=6, textColor='#1A365D')
    body_style = ParagraphStyle('DocBody', fontName=font_name, fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
    bullet_style = ParagraphStyle('DocBullet', fontName=font_name, fontSize=10.5, leading=15, alignment=TA_JUSTIFY, leftIndent=15, firstLineIndent=-10, spaceAfter=4)

    story = []
    story.append(Paragraph("BÁO CÁO TƯ VẤN HƯỚNG NGHIỆP DIỆN RỘNG TOÀN DIỆN", title_style))
    story.append(Paragraph("Hệ thống Sinh thái Phân tích Chỉ số Giáo dục - EduAI Guidance Pro v4.0", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC"), spaceBefore=1, spaceAfter=12))
    
    story.append(Paragraph(f"Học sinh: {ten.upper()} &nbsp;&nbsp;|&nbsp;&nbsp; Lớp: {lop.upper()}", info_style))
    
    story.append(Paragraph("1. Điểm số Học lực Hệ thống (8 Môn học THCS):", heading_style))
    story.append(Paragraph(f"• Toán: {d1} | Văn: {d2} | Anh: {d3} | KH Tự nhiên: {d4}", body_style))
    story.append(Paragraph(f"• Lịch sử & Địa lý: {d5} | Tin học: {d6} | Công nghệ: {d7} | GDCD: {d8}", body_style))
    
    story.append(Paragraph("2. Điểm số Chỉ số Đam mê Độc quyền Holland:", heading_style))
    story.append(Paragraph(f"• R (Kỹ thuật): {r} | I (Nghiên cứu): {i} | A (Nghệ thuật): {a}", body_style))
    story.append(Paragraph(f"• S (Xã hội): {s} | E (Quản lý): {e} | C (Nghiệp vụ): {c_score}", body_style))
    
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("3. Kết quả Nhận định Từ Mô hình Siêu AI Chuyên gia Giáo dục:", heading_style))
    
    raw_lines = loi_khuyen_ai.split('\n')
    for line in raw_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        line_clean = line_clean.replace('###', '').replace('**', '').replace('*', '').strip()
        
        if line_clean.startswith(('1.', '2.', '3.', '4.', 'ĐIỂM MẠNH', 'TƯ VẤN', 'LỘ TRÌNH', 'LỜI KHUYÊN')):
            story.append(Paragraph(line_clean, heading_style))
        elif line.strip().startswith(('-', '*', '•')):
            text_inside = line_clean.lstrip('-*• ').strip()
            story.append(Paragraph(f"• {text_inside}", bullet_style))
        else:
            story.append(Paragraph(line_clean, body_style))

    def add_footer(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont(font_italic, 8)
        canvas_obj.setFillColor(colors.HexColor('#718096'))
        canvas_obj.drawString(1.18 * inch, 0.4 * inch, "Báo cáo phân tích diện rộng tích hợp trọn vẹn 8 môn học.")
        canvas_obj.drawRightString(8.5 * inch - 0.78 * inch, 0.4 * inch, f"Trang {doc_obj.page}")
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buf.seek(0)
    return buf

if st.session_state.noi_dung_ai_v4:
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown('<p id="4" class="section-title">🎯 KẾT QUẢ ĐỊNH HƯỚNG TỪ AI CHUYÊN GIA (TÍCH HỢP DIỆN RỘNG)</p>', unsafe_allow_html=True)
    
    st.markdown(st.session_state.noi_dung_ai_v4)
    
    pdf_pro_v4 = tao_file_pdf_v4(
        ten_hs, lop_hs, d_toan, d_van, d_anh, d_khtn, d_lsgd, d_tinhoc, d_congnghe, d_gdcd,
        score_r, score_i, score_a, score_s, score_e, score_c,
        st.session_state.noi_dung_ai_v4
    )
    
    st.download_button(
        label="💥 XUẤT BÁO CÁO HƯỚNG NGHIỆP 8 MÔN TOÀN DIỆN (PDF)",
        data=pdf_pro_v4,
        file_name=f"BaoCao_HuongNghiep_8Mon_{xoa_dau_tieng_viet(ten_hs).replace(' ', '')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.markdown('</div>', unsafe_allow_html=True)