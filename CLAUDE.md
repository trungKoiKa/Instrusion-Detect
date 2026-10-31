# CLAUDE.md – ĐATN Nhóm 17: Hệ thống phát hiện người xâm nhập

Đọc file này đầu mỗi phiên. Thiết kế đầy đủ: @docs/de_xuat_trien_khai_DATN_nhom17_12.md
Những gì đã trao đổi và lý do các quyết định: @docs/tom_tat_trao_doi.md

## Dự án
- Đồ án tốt nghiệp PTIT, nhóm 2 người: Hoàng Trung Anh (phía Pi, mô hình, dữ liệu), Nguyễn Nhật Thăng (ESP32, giám sát camera, broker, watchdog).
- Raspberry Pi 4 + webcam Logitech C270 (USB) chạy YOLO11n NCNN, ảnh 320 px, chỉ lớp người. Pi gửi cảnh báo qua MQTT (Mosquitto chạy trên Pi) tới ESP32 bật đèn, còi, nhận nút xác nhận (ACK). Chạy trong WiFi nội bộ, không cần Internet.
- Hạn nộp quyển 06/12/2026. Mốc: 03/11 YOLO chạy trên Pi; 10/11 lõi đầu-cuối; 17/11 fine-tune lần đầu; 24/11 số liệu chương 3; 01/12 hoàn thiện báo cáo.

## Quyết định đã chốt (không tự ý đổi)
- Camera đặt ngang, cao khoảng 1,6 m. Khung hình chia **4 khu dọc**; khu của người xét theo **tâm ngang bbox**; file cấu hình chọn khu cấm. Không dùng ROI đa giác hay điểm chân.
- Báo động khi cửa sổ T giây của một khu cấm có đủ K_min lần thấy người và tỷ lệ ≥ p. Chọn tham số trên val, không bao giờ trên test.
- **Không có chế độ canh gác (arm/disarm)**: chương trình chạy là canh gác. Arm/disarm, RTC chỉ là mở rộng.
- Hai trạng thái độc lập: xâm nhập và quan sát camera. Pi giữ trạng thái, ESP32 chỉ làm theo. Khung không quan sát được không bao giờ coi là "không có người".
- Fine-tune cho **người xa, bị che một phần, góc nhìn lạ, cúi/ngồi**. **Không làm thiếu sáng**, không chặn trần phơi sáng; camera để phơi sáng tự động, chỉ cố định MJPG 640×480 30 fps, 50 Hz.
- Tập test: `test_normal`, `test_hard` (nhãn `far`, `occluded`, `angle`, `pose`), `test_external` (COCO val2017 đã lọc).

## Cấu trúc
- `pi/safecam/`: chương trình chính (camera, detector, zones, intrusion, observation, outputs, persistence, mqtt_client, stream, main). `pi/tests/`: pytest, chạy được trên laptop không cần phần cứng.
- `config/` cấu hình dùng chung · `esp32/` firmware · `tools/` script phụ · `ml/` notebook Colab · `deploy/` systemd, Mosquitto · `hardware/` PCB · `data/` không lên git.

## Môi trường
- Code viết trên laptop Windows. Pi (Raspberry Pi OS) chỉ `git pull` về để chạy; người dùng tự chạy lệnh trên Pi qua SSH, Claude không tự SSH.
- Train trên Google Colab.

## Quy ước
- Tên biến, hàm, file: tiếng Anh. Comment, docstring, tài liệu, commit message: tiếng Việt.
- Tài liệu **ngắn, dễ hiểu**; chi tiết cài đặt để trong code/README, không nhồi vào bản đề xuất.
- Không thêm tính năng ngoài đề xuất; cần thì đề xuất và chờ đồng ý.

## Git
- Mỗi phần việc một nhánh (`feat/...`, `fix/...`, `docs/...`, `chore/...`) và **một PR riêng** vào `main`.
- Làm tới đâu commit tới đó. **Không xóa nhánh** sau khi merge (đồ án cần giữ lịch sử).
- **Không thêm dòng `Co-Authored-By: Claude`** hay "Generated with Claude Code" vào commit hoặc PR.
- Trước khi commit: chạy `pytest pi/tests` nếu có sửa code Python.
