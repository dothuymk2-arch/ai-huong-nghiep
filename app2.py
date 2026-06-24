import streamlit as st
import sqlite3
import google.generativeai as genai
import plotly.graph_objects as go
import io

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="AI Tư Vấn Hướng Nghiệp", layout="wide")
# Đảm bảo đã thiết lập API Key trong Streamlit Secrets hoặc biến môi trường
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. GIAO DIỆN CHÍNH ---
st.title("🎓 HỆ THỐNG TƯ VẤN HƯỚNG NGHIỆP 8 MÔN")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Thông tin học sinh")
    ten = st.text_input("Họ và tên:")
    lop = st.text_input("Lớp:")
    
    st.subheader("📊 Điểm học tập (8 môn)")
    c1, c2 = st.columns(2)
    toan = c1.number_input("Toán", 0.0, 10.0)
    van = c2.number_input("Văn", 0.0, 10.0)
    anh = c1.number_input("Anh", 0.0, 10.0)
    khtn = c2.number_input("KHTN", 0.0, 10.0)
    ls_dia = c1.number_input("Sử & Địa", 0.0, 10.0)
    tin = c2.number_input("Tin học", 0.0, 10.0)
    cn = c1.number_input("Công nghệ", 0.0, 10.0)
    gdcd = c2.number_input("GDCD", 0.0, 10.0)

with col2:
    st.subheader("🧬 Chỉ số Holland")
    h_cols = st.columns(3)
    r = h_cols[0].slider("R", 0, 5, 3)
    i = h_cols[1].slider("I", 0, 5, 3)
    a = h_cols[2].slider("A", 0, 5, 3)
    s = h_cols[0].slider("S", 0, 5, 3)
    e = h_cols[1].slider("E", 0, 5, 3)
    c_holland = h_cols[2].slider("C", 0, 5, 3)
    
    if st.button("✨ KÍCH HOẠT TƯ VẤN"):
        prompt = f"Học sinh {ten} lớp {lop}. Điểm 8 môn: {toan}, {van}, {anh}, {khtn}, {ls_dia}, {tin}, {cn}, {gdcd}. Holland: R{r}, I{i}, A{a}, S{s}, E{e}, C{c_holland}. Hãy tư vấn hướng nghiệp."
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        st.session_state.ket_qua = response.text
        st.success("Đã phân tích xong!")

if "ket_qua" in st.session_state:
    st.markdown(st.session_state.ket_qua)