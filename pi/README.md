# pi – chương trình chạy trên Raspberry Pi

Trên Pi, bình thường chạy bằng dịch vụ systemd `safecam` (cài, xem log, tắt: `deploy/README.md`). Chạy tay `python -u -m safecam.main` (từ thư mục `pi/`) chỉ khi đo hoặc thử, và phải `sudo systemctl stop safecam` trước. Test: `python -m pytest pi/tests` từ gốc repo (chạy được trên laptop, không cần phần cứng).

## Cài trên Pi

```
mkdir -p ~/tmp && export TMPDIR=~/tmp   # /tmp nằm trong RAM (~2 GB), không đủ cho pip
python3 -m venv .venv && source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r pi/requirements.txt   # đã chặn opencv-python<5; cài lại sau mỗi lần git pull để có gói mới
```

Mật khẩu MQTT: chép `.env.example` (gốc repo) thành `.env`, điền `SAFECAM_MQTT_PASS`. `.env` không lên git.

Xem luồng hình (demo): đặt `enabled: true` trong `config/stream.yaml`, chạy `main.py`, trên laptop cùng WiFi mở `http://<ip-pi>:8080`. Không có mật khẩu, chỉ dùng trong mạng nội bộ; chạy nền đo đạc thì đặt `false`. Ảnh hưởng tới FPS: `docs/do_dac/stream_fps.md`.

Phải cài torch bản CPU trước: bản mặc định trên PyPI kéo theo vài GB thư viện CUDA vô dụng trên Pi và làm đầy thẻ 32 GB.

| Module | Việc | Mục đề xuất (bản 12) |
| --- | --- | --- |
| `camera.py` | Luồng đọc C270, giữ khung mới nhất, mã khung, tự mở lại | 3 |
| `detector.py` | YOLO11n NCNN imgsz 320, chỉ lớp người | 3 |
| `zones.py` | Xác định khu theo tâm ngang bbox, cửa sổ T giây từng khu | 3 |
| `intrusion.py` | Trạng thái xâm nhập | 5 |
| `observation.py` | Giám sát camera và trạng thái quan sát (Thăng) | 5 |
| `outputs.py` | Bảng ưu tiên đèn/còi | 5 |
| `persistence.py` | Ghi file trạng thái mỗi lần đổi, khôi phục khi khởi động lại | 5 |
| `mqtt_client.py` | Publish event/state/hb, nhận ACK | 6 |
| `stream.py` | Luồng hình có vẽ khu và khung người, xem trên laptop khi demo | 8 |
| `sdnotify.py` | Báo systemd `READY=1`, `WATCHDOG=1`; chạy tay thì không làm gì (Thăng) | 9 |
| `main.py` | Ghép các module, vòng suy luận; `systemctl stop` (SIGTERM) tắt gọn như Ctrl+C | – |
