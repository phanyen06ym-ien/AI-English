import cv2

print("Đang kiểm tra camera...")

for index in range(5):
    cap = cv2.VideoCapture(index)

    if cap.isOpened():
        print(f"Camera {index}: Hoạt động")
        cap.release()
    else:
        print(f"Camera {index}: Không hoạt động")