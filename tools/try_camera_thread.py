import sys, time
sys.path.insert(0, "pi")
from safecam.config import load_config
from safecam.camera import Camera

cfg = load_config("camera")
if sys.platform == "win32":
    cfg["device"] = 0
cam = Camera(cfg)
cam.start()
last = 0
done = 0
while done < 300:
    got = cam.get_latest(last)
    if got is None:
        print("Mất hình quá 2s")
        continue
    seq, img = got
    print("Xử lý ảnh số", seq, "bỏ qua", seq - last -1)
    last = seq
    time.sleep(0.2) # giả làm YOLO mất 0.2s
cam.stop()