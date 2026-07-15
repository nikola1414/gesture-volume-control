# type: ignore
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

landmark_style = mp_draw.DrawingSpec(
    color=(7, 69, 12),   
    thickness=2,          
    circle_radius=4       
)

connection_style = mp_draw.DrawingSpec(
    color=(89, 162, 95), 
    thickness=2          
)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)
cv2.namedWindow("Hand Tracker", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Hand Tracker", 1280, 720)

while True:
    success, img = cap.read()
    
    if not success:
        print("kurcina")
        break

    img = img.copy()
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                img, 
                hand_lms,
                mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec = landmark_style,
                connection_drawing_spec = connection_style
                )
    
    cv2.imshow("Hand Tracker", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()