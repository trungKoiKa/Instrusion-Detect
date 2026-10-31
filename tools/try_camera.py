import sys
sys.path.insert(0, "pi") # để import được safecam
import cv2
from safecam.config import load_config
from safecam.camera import open_camera

cfg = load_config("camera")
cfg["device"] = 0 # chỉ dùng trên laptop, trên pi bỏ
cap = open_camera(cfg)
print("Mở được: ", cap.isOpened())
w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Kích thước thật: {w:.0f}x{h:.0f}, fps: {fps:.0f}")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Mất hình")
        break
    cv2.imshow("thu camera", frame)
    if cv2.waitKey(1) == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()