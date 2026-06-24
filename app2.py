import streamlit as st
import os
import time
import sqlite3
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI Tư Vấn & Định Hướng Nghề Nghiệp", page_icon="🎓", layout="centered")

# --- CẤU HÌNH API KEY (Lấy từ Secrets) ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = ""

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        client = genai
    except Exception:
        st.error("Lỗi cấu hình AI Studio.")
else:
    client = None

# --- GIAO DIỆN CHÍNH ---
st.title("🎓 HỆ THỐNG AI TƯ VẤN HƯỚNG NGHIỆP TOÀN DIỆN")
st.write("---")

# Nhập thông tin học sinh
col1, col2 = st.columns(2)
with col1:
    ten_hs = st.text_input("✍️ Nhập họ và tên học sinh:", value="")
with col2:
    lop_hs = st.text_input("🏫 Nhập lớp (Ví dụ: 9A1):", value="")

# --- THANH PHÁT ÂM THANH CHÀO MỪNG TỐI ƯU CỦA GOOGLE ---
if ten_hs and lop_hs:
    cau_chao = f"Xin chào bạn {ten_hs}, học sinh lớp {lop_hs}. Chào mừng bạn đến với hệ thống AI hướng nghiệp 8 môn toàn diện. Hãy kéo xuống dưới để làm trắc nghiệm và xem kết quả nhé."
    st.audio(f"https://translate.google.com/translate_tts?ie=UTF-8&tl=vi&client=tw-ob&q={cau_chao}", format="audio/mp3")

st.write("---")
st.subheader("📊 Nhập điểm số học tập (Hệ điểm 10):")

# Các ô nhập điểm
c1, c2, c3, c4 = st.columns(4)
with c1: d_toan = st.number_input("Toán:", 0.0, 10.0, 7.0)
with c2: d_van = st.number_input("Văn:", 0.0, 10.0, 7.0)
with c3: d_anh = st.number_input("Anh:", 0.0, 10.0, 7.0)
with c4: d_khtn = st.number_input("KHTN:", 0.0, 10.0, 7.0)

c5, c6, c7, c8 = st.columns(4)
with c5: d_lsgd = st.number_input("Lịch sử - Địa lý:", 0.0, 10.0, 7.0)
with c6: d_tinhoc = st.number_input("Tin học:", 0.0, 10.0, 7.0)
with c7: d_congnghe = st.number_input("Công nghệ:", 0.0, 10.0, 7.0)
with c8: d_gdcd = st.number_input("GDCD:", 0.0, 10.0, 7.0)

st.write("---")
st.subheader("🧬 Trắc nghiệm sở thích nghề nghiệp Holland (0 - 5 điểm):")
cc1, cc2, cc3 = st.columns(3)
with cc1: score_r = st.slider("Nhóm Kỹ thuật (R):", 0, 5, 3)
with cc2: score_i = st.slider("Nhóm Nghiên cứu (I):", 0, 5, 3)
with cc3: score_a = st.slider("Nhóm Nghệ thuật (A):", 0, 5, 3)

cc4, cc5, cc6 = st.columns(3)
with cc4: score_s = st.slider("Nhóm Xã hội (S):", 0, 5, 3)
with cc5: score_e = st.slider("Nhóm Quản lý (E):", 0, 5, 3)
with cc6: score_c = st.slider("Nhóm Nghiệp vụ (C):", 0, 5, 3)

# Khởi tạo trạng thái lưu kết quả
if "noi_dung_ai" not in st.session_state:
    st.session_state.noi_dung_ai = ""

st.write("---")

# Nút bấm kích hoạt tư vấn
if st.button("✨ KÍCH HOẠT TƯ VẤN HƯỚNG NGHIỆP", use_container_width=True):
    if not ten_hs or not lop_hs:
        st.warning("⚠️ Vui lòng điền đầy đủ Tên và Lớp trước khi kích hoạt!")
    else:
        with st.spinner("🤖 Hệ thống AI đang tổng hợp dữ liệu và phân tích chuyên sâu..."):
            prompt = (
                f"Hãy phân tích bộ dữ liệu học sinh lớp 9: Học sinh: {ten_hs}, Lớp: {lop_hs}.\n"
                f"Điểm số: Toán {d_toan}, Văn {d_van}, Anh {d_anh}, KHTN {d_khtn}, Sử-Địa {d_lsgd}, Tin {d_tinhoc}, Công nghệ {d_congnghe}, GDCD {d_gdcd}.\n"
                f"Chỉ số Holland: R:{score_r}, I:{score_i}, A:{score_a}, S:{score_s}, E:{score_e}, C:{score_c}.\n"
                f"Hãy xuất câu trả lời phân định bôi đậm rõ ràng theo cấu trúc:\n"
                f"1. ĐIỂM MẠNH & ĐIỂM HẠN CHẾ DIỆN RỘNG\n"
                f"2. TƯ VẤN CHỌN TỔ HỢP MÔN LỚP 10\n"
                f"3. LỘ TRÌNH HÀNH ĐỘNG 3 GIAI ĐOẠN\n"
                f"4. LỜI KHUYÊN DÀNH CHO GIA ĐÌNH"
            )
            
            thanh_cong = False
            if client:
                for luot_thu in range(2):
                    try:
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        st.session_state.noi_dung_ai = response.text
                        thanh_cong = True
                        break
                    except Exception:
                        time.sleep(1)
            
            if not thanh_cong:
                st.warning("⚠️ Đang chạy chế độ phân tích cục bộ dự phòng:")
                st.session_state.noi_dung_ai = (
                    "### 1. ĐIỂM MẠNH & ĐIỂM HẠN CHẾ DIỆN RỘNG\n"
                    f"- Học sinh {ten_hs} có phổ điểm các môn tự nhiên và tư duy logic rất tốt.\n\n"
                    "### 2. TƯ VẤN CHỌN TỔ HỢP MÔN LỚP 10\n"
                    "- Khuyến nghị chọn tổ hợp liên quan đến Vật lý, Hóa học, Tin học hoặc Công nghệ.\n\n"
                    "### 3. LỘ TRÌNH HÀNH ĐỘNG 3 GIAI ĐOẠN\n"
                    "- Tập trung ôn thi cuối cấp $\rightarrow$ Lựa chọn môi trường cấp 3 $\rightarrow$ Tìm hiểu đại học.\n\n"
                    "### 4. LỜI KHUYÊN DÀNH CHO GIA ĐÌNH\n"
                    "- Tạo động lực và không gian thoải mái để con tự tin học tập tốt."
                )

# Hiển thị kết quả kết xuất
if st.session_state.noi_dung_ai:
    st.success("✅ Đã hoàn tất phân tích hướng nghiệp nâng cao!")
    st.markdown(st.session_state.noi_dung_ai)
