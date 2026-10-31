# pi – chương trình chạy trên Raspberry Pi

Chạy: `python -m safecam.main` (từ thư mục `pi/`). Test: `pytest tests/` (chạy được trên laptop, không cần phần cứng).

| Module | Việc | Mục đề xuất |
| --- | --- | --- |
| `camera.py` | Luồng đọc C270, giữ khung mới nhất, mã khung, tự mở lại | 3 |
| `detector.py` | YOLO11n NCNN imgsz 320, chỉ lớp người | 3 |
| `zones.py` | Xác định khu theo tâm ngang bbox, cửa sổ T giây từng khu | 3 |
| `intrusion.py` | Trục xâm nhập | 5.2 |
| `observation.py` | Giám sát quan sát và trục quan sát (Thăng) | 5.3, 6 |
| `outputs.py` | Bảng ưu tiên đèn/còi | 5.5 |
| `persistence.py` | Lưu bền file trạng thái, boot_id/seq | 5.6 |
| `mqtt_client.py` | Publish event/state/hb, nhận ACK | 7 |
| `stream.py` | Luồng hình demo trên trình duyệt (tắt được) | 9 |
| `main.py` | Ghép các module, vòng suy luận | – |
