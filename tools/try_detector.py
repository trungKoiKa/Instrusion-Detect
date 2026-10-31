import sys
sys.path.insert(0, "pi")
import cv2 
from safecam.config import load_config
from safecam.detector import PersonDetector
from safecam.camera import Camera

cam_cfg = load_config("camera")
det_cfg = load_config("detection")

if sys.platform == "win32":
    cam_cfg["device"] = 0 # laptop: webcam may
    model = "yolo11n.pt" # laptop: mo hinh Pytorch, tu tai ve
else:
    model = det_cfg["model"] # Pi: thu muc NCNN da export

print("Dang nap model", model)
det = PersonDetector(model, det_cfg["imgsz"], det_cfg["conf"])
cam = Camera(cam_cfg)
cam.start()

last = 0
while True:
    got = cam.get_latest(last)
    if got is None:
        print("Mat hinh qua 2s")
        continue
    last, img = got
    people = det.detect(img)

    # Ve khung xanh quang nguoi (bounding box)
    for p in people:
        cv2.rectangle(img, (int(p.x1), int(p.y1)), (int(p.x2), int(p.y2)), (0, 255, 0), 2)
        cv2.putText(img, f"{p.conf:.2f}", (int(p.x1), int(p.y1) - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
        # Dong thong tin o goc tren
    cv2.putText(img, f"person: {len(people)} YOLO {det.speed['inference']:.0f}ms",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Detected Person", img)
    if cv2.waitKey(1) == ord("q"):
        break
cam.stop()
cv2.destroyAllWindows()