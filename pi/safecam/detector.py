from dataclasses import dataclass

import numpy as np
from ultralytics import YOLO

@dataclass
class Detection:
    """Một người phát hiện được: tọa độ khung và độ tin cậy. """
    x1: float
    y1: float 
    x2: float
    y2: float
    conf: float

    @property
    def cx(self):
        """ Tầm ngang của khung, dùng để biết người ở khu nào. """
        return (self.x1 + self.x2) / 2
    
class PersonDetector:
    """ Phát hiện người bằng YOLO11n, chỉ lấy lớp người (lớp 0). """

    def __init__(self, model_path, imgsz=320, conf=0.25):
        self.model = YOLO(model_path, task="detect")
        self.imgsz = imgsz
        self.conf = conf
        self.speed = {}
        # Chạy mỗi một lần: lần đầu luôn chậm, không tính vào số đo
        self.detect(np.zeros((480, 640, 3), dtype=np.uint8))

    def detect(self, image):
        r = self.model.predict(image, imgsz=self.imgsz, conf=self.conf, 
                                classes=[0], verbose=False)[0]
        self.speed = r.speed # ms: preprocess, inference, postprocess
        boxes = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        return [Detection(*b, c) for b, c in zip(boxes, confs)]