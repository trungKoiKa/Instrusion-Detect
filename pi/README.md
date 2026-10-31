# pi – chương trình chạy trên Raspberry Pi

Chạy: `python -m safecam.main` (từ thư mục `pi/`). Test: `pytest tests/` (chạy được trên laptop, không cần phần cứng).

## Cài trên Pi

```
mkdir -p ~/tmp && export TMPDIR=~/tmp   # /tmp nằm trong RAM (~2 GB), không đủ cho pip
python3 -m venv .venv && source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r pi/requirements.txt
```

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
| `main.py` | Ghép các module, vòng suy luận | – |
