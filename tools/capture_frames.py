"""Tự chụp ảnh từ C270 để làm dữ liệu fine-tune, mỗi lần chạy là một phiên.

Ảnh lưu vào data/raw/<phiên>/<phiên>_0001.jpg, ... Camera mở qua safecam.camera
nên có đúng cấu hình như lúc chạy thật (MJPG 640x480, 30 fps, 50 Hz).

Chạy từ thư mục gốc dự án:
    python tools/capture_frames.py --session s01            # 110 giây, 2 ảnh/giây = 220 ảnh
    python tools/capture_frames.py --session s01 --show     # có cửa sổ xem hình, bấm q để dừng sớm
Dừng sớm khi không có cửa sổ: Ctrl+C (ảnh đã chụp vẫn giữ).
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # thư mục gốc dự án
sys.path.insert(0, str(ROOT / "pi"))

import cv2
from safecam.config import load_config
from safecam.camera import Camera


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True, help="tên phiên, ví dụ s01 (ảnh cả phiên vào cùng một tập)")
    ap.add_argument("--seconds", type=float, default=110, help="thời gian chụp (giây)")
    ap.add_argument("--rate", type=float, default=2, help="số ảnh mỗi giây")
    ap.add_argument("--delay", type=float, default=5, help="đếm ngược trước khi chụp (giây)")
    ap.add_argument("--show", action="store_true", help="hiện cửa sổ hình (cần màn hình)")
    args = ap.parse_args()

    # Không ghi đè phiên cũ: lỡ gõ trùng tên thì dừng ngay
    out = ROOT / "data" / "raw" / args.session
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} đã có ảnh. Đổi tên phiên hoặc tự xóa thư mục cũ.")
    out.mkdir(parents=True, exist_ok=True)

    cfg = load_config("camera")
    if sys.platform == "win32":
        cfg["device"] = 0           # laptop: webcam máy

    total = int(args.seconds * args.rate)
    interval = 1 / args.rate
    cam = Camera(cfg)
    cam.start()

    for s in range(int(args.delay), 0, -1):
        print(f"Bắt đầu sau {s} giây...")
        time.sleep(1)
    print(f"Chụp {total} ảnh vào {out}")

    last_seq = 0
    count = 0
    next_t = time.monotonic()
    try:
        while count < total:
            got = cam.get_latest(last_seq)
            if got is None:
                print("Mất hình quá 2 giây, chờ camera mở lại")
                continue
            last_seq, img = got
            count += 1
            cv2.imwrite(str(out / f"{args.session}_{count:04d}.jpg"), img,
                        [cv2.IMWRITE_JPEG_QUALITY, 95])
            if count % 20 == 0 or count == total:
                print(f"{count}/{total}")

            if args.show:
                cv2.imshow("capture", img)
                if cv2.waitKey(1) == ord("q"):
                    break

            # Giữ nhịp đều: chụp theo lịch, không theo lúc vòng lặp chạy xong
            next_t += interval
            time.sleep(max(0, next_t - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()
        cv2.destroyAllWindows()
    print(f"Xong: {count} ảnh trong {out}")


if __name__ == "__main__":
    main()
