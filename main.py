# type: ignore
import cv2
import time
import numpy as np
import handModule as hm


cap = cv2.VideoCapture(0)
cv2.namedWindow("Volume Controler", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Volume Controler", 1280, 720)

detector = hm.handDetector()

while True:
    success, img = cap.read()
    
    if not success:
        print("kurcina")
        break

    img = detector.findHands(img)

    
    cv2.imshow("Volume Controler", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()