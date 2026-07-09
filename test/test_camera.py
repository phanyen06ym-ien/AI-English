import cv2

for i in range(5):
    print(f"\n===== Camera {i} =====")

    cap = cv2.VideoCapture(i)

    print("Opened:", cap.isOpened())

    if cap.isOpened():
        ret, frame = cap.read()
        print("Read:", ret)

        if ret:
            cv2.imshow(f"Camera {i}", frame)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()

    cap.release()