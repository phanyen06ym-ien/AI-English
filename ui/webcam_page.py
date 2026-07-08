import streamlit as st
import cv2

st.title("Camera Detection")
run = st.checkbox('Mở Webcam')
FRAME_WINDOW = st.image([])
camera = cv2.VideoCapture(0)

if run:
    while run:
        _, frame = camera.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        FRAME_WINDOW.image(frame)
else:
    camera.release()