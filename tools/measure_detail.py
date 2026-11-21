""" Đo độ chi tiết ảnh (image_detail) từ cam để chọn ngướng "camera bị che".

Chạy từ thư mục gốc dự án, mỗi cảnh một lần:
    python tools/measure_detail.py --device 1 --show #laptop
    python tools/measure_detail.py  #PI
Hết giờ hoặc Ctrl + C thì in nhỏ nhất/ giữa / lớn nhất"""

import argparse
import statistics
import sys
import time
from pathlib import Path 

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pi"))

import cv2
from safecam.camera import Camera
from safecam.config import load_config
from safecam.observation import image_detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=20, help="thời gian đo mỗi cảnh (giây)")
    ap.add_argument("--device", type=int, default=0, help="số camera trên Windows (0, 1, ...)")
    ap.add_argument("--show", action="store_true", help="hiện cửa sổ hình, bấm q để dừng")
    args = ap.parse_args()

    cfg = load_config("camera")
    if sys.platform == "win32":
        cfg["device"] = args.device

    cam = Camera(cfg)
    cam.start()
    values = []
    last_seq = 0
    end = time.monotonic() + args.seconds
    try:
        while time.monotonic() < end:
            got = cam.get_latest(last_seq)
            if got is None:
                print("Mất hình quá 2s")
                continue
            last_seq, img = got
            d = image_detail(img)
            values.append(d)
            print(f"{d:6.1f}")
            if args.show:
                cv2.putText(img, f"{d:.1f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
                cv2.imshow("detail", img)
                if cv2.waitKey(1) == ord("q"):
                    break
            time.sleep(0.5) # khoảng 2 số mỗi giây là đủ
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()
        cv2.destroyAllWindows()

    if values: 
        print(f"{len(values)} ảnh: nhỏ nhất {min(values):.1f}, "
              f"giữa {statistics.median(values):.1f}, lớn nhất {max(values):.1f}")

if __name__ == "__main__":
    main()