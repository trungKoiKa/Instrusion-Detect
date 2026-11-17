import cv2
import subprocess
import threading
import time 
import sys 

def apply_v4l2_controls(cfg):                                        
    """Áp các control mà OpenCV không đặt được (tần số điện lưới).
    Chỉ chạy trên Linux; trên laptop Windows thì bỏ qua."""
    if not sys.platform.startswith("linux"):
        return
    cmd = ["v4l2-ctl", "-d", str(cfg["device"]),
           "-c", f"power_line_frequency={cfg['power_line_frequency']}"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError) as e:
        print("Không chạy được v4l2-ctl:", e)
        return
    if r.returncode != 0:
        print("Không đặt được power_line_frequency:", r.stderr.strip())


def open_camera(cfg):
    if sys.platform.startswith("linux"):
        backend = cv2.CAP_V4L2          # Pi
    elif sys.platform == "win32":
        backend = cv2.CAP_DSHOW         # laptop: MSMF (mặc định) treo khi mở C270
    else:
        backend = cv2.CAP_ANY
    cap = cv2.VideoCapture(cfg["device"], backend)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cfg["fourcc"]))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg["height"])
    cap.set(cv2.CAP_PROP_FPS, cfg["fps"])
    if cap.isOpened():
        apply_v4l2_controls(cfg)
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