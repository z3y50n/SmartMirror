import os

import cv2


class FaceRecognition():
    def __init__(self, model, control, active=True, camera=0):
        self._model = model
        self._active = active
        self._camera = camera
        self._faceCascade = cv2.CascadeClassifier(self._model)
        self._video_capture = cv2.VideoCapture(self._camera)

    def _check_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self._faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) > 0:
            return True
        return False
        

    def face_detect(self):
        ret, frame = self._video_capture.read()

        return self._check_face(frame)
