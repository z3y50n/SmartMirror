import os

import cv2

from basedir import BASEDIR

class FaceRecognition:
    def __init__(self, model, camera=0):
        self._model = model
        self._camera = camera

    def face_recognition(self):
        faceCascade = cv2.CascadeClassifier(self._model)
        video_capture = cv2.VideoCapture(self._camera)

        while True:
            ret, frame = video_capture.read()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.imshow("Video", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    model = os.path.join(BASEDIR, "assets", "facial_recognition_model.xml")
    FR = FaceRecognition(model)
    FR.face_recognition()

