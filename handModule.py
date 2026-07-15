# type: ignore
import cv2
import mediapipe as mp

class handDetector():
    def __init__(self,staticMode = False, maxHands = 2, detectionCon =0.5, trackCon = 0.5):
        self.mode = staticMode 
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.landmark_style = self.mp_draw.DrawingSpec(
            color=(7, 69, 12),   
            thickness=2,          
            circle_radius=4       
        )

        self.connection_style = self.mp_draw.DrawingSpec(
            color=(89, 162, 95), 
            thickness=2          
        )       

        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode, 
            max_num_hands=self.maxHands, 
            min_detection_confidence=self.detectionCon, 
            min_tracking_confidence=self.trackCon
        )

    def findHands(self,img , draw = True):
        img = img.copy()
        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
        self.results = self.hands.process(img_rgb)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        img, 
                        handLms,
                        self.mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec = self.landmark_style,
                        connection_drawing_spec = self.connection_style
                )
        return img

    def findPositioning(self, img, handNo=0, draw = True):
        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h,w,c = img.shape
                cx , cy = int(lm.x*w), int(lm.y*h)
                lmList.append([id,cx,cy])
                if draw:
                    cv2.circle(img,(cx,cy), 15, (255,0,255), cv2.FILLED)
        return lmList


""""
def main():
    pTime = 0
    cTime = 0
    cap = cv2.videoCapture
    detector = handDetector()
    while True: 
        success, img = cap.read()
        img = detector.findHands(img)
        lmList = detector.findPostioning(img)
        if len(lmList)!=0:
            print(lmList[4])



if __name__ == "__main__":
    main()
"""