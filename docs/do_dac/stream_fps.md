# Ảnh hưởng của luồng hình (stream) tới tốc độ trên Pi

Đo 24–25/11/2026 trên Raspberry Pi 4, mô hình gốc YOLO11n NCNN 320 px, `main.py` đầy đủ (camera, YOLO, 4 khu, MQTT).
Mỗi lần chạy 320 giây (`timeout 320`), `main.py` in FPS mỗi 30 giây; bỏ giá trị đầu (lúc mở camera).
FPS ở đây là số ảnh vòng lặp chính nhận được mỗi giây, không so trực tiếp với số đo của `tools/bench_pi.py`.

| Lần | Giờ | Stream | Laptop xem | FPS trung bình | FPS nhỏ nhất | Số giá trị | Nhiệt độ cuối | Hạ xung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 23:48–23:53 | tắt | – | 8,29 | 8,27 | 9 | 36,5 °C | 0x0 |
| B | 23:55–00:00 | bật | không | 8,28 | 8,24 | 9 | 32,6 °C | 0x0 |
| C | 00:02–00:07 | bật | có | 8,23 | 8,17 | 6 | 38,9 °C | 0x0 |

**Lần C:** trong lúc đo có người vào khu 2 (I63–I66) và che camera 2 lần (O14, O15). Lúc camera bị che, `main.py` không chạy YOLO nên FPS lên 8,72–10,58; 3 khoảng 30 giây có che bị loại, còn 6 khoảng. Việc laptop xem suốt lần C do người đo xác nhận, không có kết quả `ss` trong lúc đo.

**Kết luận:**
- Bật stream mà không ai xem: FPS không đổi (8,29 → 8,28).
- Có laptop xem: FPS giảm 0,06 (khoảng 0,7%); nhỏ nhất 8,17, vẫn gấp đôi mức 4 FPS mà cửa sổ T giây cần (`n_min / window_s`). Bật stream khi demo là an toàn.
- Khi camera bị che, FPS tăng lên ~10: YOLO là phần chậm nhất của vòng lặp.

**Giới hạn:** mỗi trường hợp đo một lần, 5 phút; một laptop xem; lần C cảnh không đứng yên như A và B.

Log trên Pi: `data/fps_A.log`, `fps_B.log`, `fps_C.log` (không lên git).
