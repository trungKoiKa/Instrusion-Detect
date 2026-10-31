# esp32 – firmware trạm cảnh báo (Thăng)

Đề xuất: PlatformIO + Arduino framework + PubSubClient (cần nhóm chốt). Chức năng: nhận `state`/`event`, bật đèn/còi theo bảng ưu tiên, nút ACK gửi lặp lại, phát hiện mất heartbeat, hiển thị khu đang có xâm nhập.

WiFi và mật khẩu MQTT để trong `include/secrets.h` (đã gitignore).
