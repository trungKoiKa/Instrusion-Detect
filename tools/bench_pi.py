"""Đo hiệu năng YOLO trên Pi: FPS, CPU, RAM, nhiệt độ, hạ xung. Mỗi giây ghi 1 dòng CSV.

Chạy từ thư mục gốc dự án:
    python tools/bench_pi.py --minutes 1 --show    # xem hình (trên màn hình Pi)
    python tools/bench_pi.py --minutes 45          # đo chính thức, không hiện hình
"""

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # thư mục gốc dự án
sys.path.insert(0, str(ROOT / "pi"))

import cv2
import psutil
from safecam.config import load_config
from safecam.camera import Camera
from safecam.detector import PersonDetector


def read_temp():
    """Nhiệt độ CPU (°C). Chỉ có trên Pi/Linux; laptop trả về rỗng."""
    try:
        return int(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000
    except (OSError, ValueError):
        return ""


def read_mhz():
    """Xung CPU hiện tại (MHz). Bị hạ xung thì số này tụt xuống."""
    try:
        return int(Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").read_text()) // 1000
    except (OSError, ValueError):
        return ""


def read_throttled():
    """vcgencmd get_throttled: 0x0 là bình thường, khác 0 là thiếu điện hoặc quá nhiệt."""
    try:
        out = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2).stdout
        return out.strip().split("=")[-1]
    except (OSError, subprocess.SubprocessError):
        return ""


def draw(img, people, text):
    """Vẽ 3 vạch chia 4 khu, khung người, tâm ngang và dòng thông tin."""
    h, w = img.shape[:2]
    for i in range(1, 4):
        x = w * i // 4
        cv2.line(img, (x, 0), (x, h), (0, 200, 255), 1)
    for i in range(4):
        cv2.putText(img, f"Khu {i}", (w * i // 4 + 5, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
    for p in people:
        cv2.rectangle(img, (int(p.x1), int(p.y1)), (int(p.x2), int(p.y2)), (0, 255, 0), 2)
        cv2.circle(img, (int(p.cx), int((p.y1 + p.y2) / 2)), 4, (0, 0, 255), -1)
    cv2.putText(img, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=1, help="thời gian đo (phút)")
    ap.add_argument("--show", action="store_true", help="hiện cửa sổ hình")
    args = ap.parse_args()

    cam_cfg = load_config("camera")
    det_cfg = load_config("detection")
    if sys.platform == "win32":
        cam_cfg["device"] = 0
        model = "yolo11n.pt"
    else:
        model = str(ROOT / det_cfg["model"])

    print("Đang nạp mô hình", model)
    det = PersonDetector(model, det_cfg["imgsz"], det_cfg["conf"])
    cam = Camera(cam_cfg)
    cam.start()

    # Mở file CSV trong thư mục logs/ (đã có trong .gitignore)
    (ROOT / "logs").mkdir(exist_ok=True)
    csv_path = ROOT / "logs" / f"bench_{datetime.now():%Y%m%d_%H%M%S}.csv"
    f = open(csv_path, "w", newline="", encoding="utf-8")
    writer = csv.writer(f)
    writer.writerow(["time", "elapsed_s", "fps", "infer_ms", "persons", "skipped_frames",
                     "cpu_percent", "ram_used_mb", "temp_c", "cpu_mhz", "throttled"])
    print("Ghi số liệu vào", csv_path)

    psutil.cpu_percent(None)            # lần gọi đầu luôn ra 0, gọi bỏ đi
    t_start = time.monotonic()
    t_end = t_start + args.minutes * 60
    t_win = t_start                     # đầu cửa sổ 1 giây hiện tại
    n = 0                               # số ảnh YOLO xử lý trong cửa sổ
    infer_sum = 0.0
    skipped = 0
    persons_max = 0
    fps = 0.0
    last = 0

    try:
        while time.monotonic() < t_end:
            got = cam.get_latest(last)
            if got is None:
                print("Mất hình quá 2 s")
                continue
            seq, img = got
            if last:
                skipped += seq - last - 1
            last = seq

            people = det.detect(img)
            n += 1
            infer_sum += det.speed["inference"]
            persons_max = max(persons_max, len(people))

            if args.show:
                text = f"FPS {fps:.1f}  YOLO {det.speed['inference']:.0f} ms  nguoi {len(people)}"
                cv2.imshow("bench", draw(img, people, text))
                if cv2.waitKey(1) == ord("q"):
                    break

            now = time.monotonic()
            if now - t_win >= 1.0:      # đủ 1 giây thì ghi 1 dòng
                fps = n / (now - t_win)
                mem = psutil.virtual_memory()
                row = [datetime.now().isoformat(timespec="seconds"),
                       round(now - t_start, 1),
                       round(fps, 2),
                       round(infer_sum / n, 1),
                       persons_max,
                       skipped,
                       psutil.cpu_percent(None),
                       round((mem.total - mem.available) / 2**20),
                       read_temp(),
                       read_mhz(),
                       read_throttled()]
                writer.writerow(row)
                f.flush()               # ghi ngay xuống thẻ, Pi tắt đột ngột không mất số liệu
                if int(now - t_start) % 10 == 0:
                    print(f"[{now - t_start:5.0f} s] FPS {fps:.1f}  YOLO {infer_sum / n:.0f} ms  "
                          f"CPU {row[6]:.0f}%  {row[8]} °C  throttled={row[10]}")
                n = 0
                infer_sum = 0.0
                skipped = 0
                persons_max = 0
                t_win = now
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()
        f.close()
        if args.show:
            cv2.destroyAllWindows()
    print("Xong. File CSV:", csv_path)


if __name__ == "__main__":
    main()