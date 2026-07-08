# ui/vocabulary_page.py
import streamlit as st

def show_vocabulary_page():
    st.title("Từ vựng đã học")
    # Danh sách giả lập (Kết nối DB ở đây nếu cần)
    data = {"Từ": ["cat", "dog"], "Độ khó": ["A1", "A1"]}
    st.table(data)