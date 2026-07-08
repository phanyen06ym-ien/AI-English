# ui/image_page.py
import streamlit as st


def show_image_page():
    st.title("Phân tích hình ảnh")
    uploaded_file = st.file_uploader("Tải lên hình ảnh vật thể:", type=["jpg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Ảnh đã tải lên", use_column_width=True)
        st.write("Đang phân tích...")
        # Ở đây bạn sẽ gọi model YOLO để xử lý ảnh