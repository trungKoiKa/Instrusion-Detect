import cv2
import threading
import time
import sys

def open_camera(cfg):
    backend = cv2.CAP_V4L2 if sys.platform.startswith("linux") else cv2.CAP_ANY
    cap = cv2.VideoCapture(cfg["device"], backend)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cfg["fourcc"]))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg["height"])
    cap.set(cv2.CAP_PROP_FPS, cfg["fps"])
    return cap


class Camera:
    def __init__(self, cfg):
        self.cfg = cfg
        self.cond = threading.Condition()
        self.frame = None #(seq, ảnh)
        self.seq = 0
        self.wanted = False # YOLO dang cho anh
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _run(self):
        cap = None
        fails = 0
        while self.running:
            if cap is None: # Chua mo hoac vua hong
                cap = open_camera(self.cfg)
                if not cap.isOpened():
                    print("Không mở được camera, thử lại sau 2s")
                    cap.release()
                    cap = None
                    time.sleep(2)
                    continue
                fails = 0
            if not cap.grab(): # lấy ảnh nén
                fails += 1
                if fails >= 30:
                    print("Camera lỗi, mở lại")
                    cap.release()
                    cap = None
                    time.sleep(2)
                else:
                    time.sleep(0.01)
                continue
            fails = 0
            self.seq += 1
            if self.wanted: #chỉ giải nén khi YOLO cần
                ok, img = cap.retrieve()
                if ok:
                    with self.cond:
                        self.frame = (self.seq, img)
                        self.wanted = False
                        self.cond.notify_all() #đánh thức YOLO
        if cap is not None:
            cap.release()

    def get_latest(self, after_seq, timeout=2.0):
        with self.cond:
            self.wanted = True
            self.cond.wait_for(lambda: self.frame is not None and self.frame[0] > after_seq, timeout)
            if self.frame is not None and self.frame[0] > after_seq:
                return self.frame
            return None