# SafeCam – Hệ thống giám sát phát hiện người xâm nhập (ĐATN Nhóm 17)

Raspberry Pi 4 + Logitech C270 chạy YOLO11n (NCNN, imgsz 320) phát hiện người trong 4 khu dọc; gửi cảnh báo qua MQTT (Mosquitto trên Pi) tới ESP32 bật đèn, còi và nhận xác nhận. Toàn bộ chạy trong mạng nội bộ.

Đọc trước: `docs/de_xuat_trien_khai_DATN_nhom17_12.md`.

| Thư mục | Nội dung | Người phụ trách |
| --- | --- | --- |
| `docs/` | Đề xuất, tóm tắt, kế hoạch, ghi chú đo đạc | Cả nhóm |
| `config/` | File cấu hình dùng chung: camera, khu, MQTT, tham số phát hiện | Cả nhóm |
| `pi/` | Chương trình Python chạy trên Pi | Trung Anh (giám sát quan sát: Thăng) |
| `esp32/` | Firmware trạm cảnh báo | Thăng |
| `tools/` | Script phụ: thu dữ liệu, hiệu chỉnh khu, đo hiệu năng, đo độ trễ | Cả nhóm |
| `ml/` | Notebook Colab, cấu hình dataset, script chuyển nhãn | Trung Anh |
| `deploy/` | systemd unit, cấu hình Mosquitto | Thăng |
| `hardware/` | PCB, sơ đồ nguyên lý | Cả nhóm |
| `data/` | Video, ảnh, dataset, model, log (không đưa lên git) | – |
