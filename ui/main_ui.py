import streamlit as st
from utils.helper import xu_ly_all
from ml.bayes import VocabularyClassifier

# Khởi tạo model
clf = VocabularyClassifier()
clf.train()

st.title("AI-English Learning")

# Đăng nhập (Sử dụng session_state)
if 'user' not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    user = st.text_input("Username")
    if st.button("Đăng nhập"):
        st.session_state.user = user
        st.rerun()
else:
    # Nhập từ (Kết quả từ Webcam truyền vào đây)
    word = st.text_input("Từ nhận diện được:")
    if word:
        level = clf.predict(word)
        meaning, audio = xu_ly_all(word)

        st.write(f"Cấp độ: **{level}**")
        st.write(f"Nghĩa: {meaning}")
        st.audio(audio)