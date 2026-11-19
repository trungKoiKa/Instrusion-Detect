# esp32 – firmware trạm cảnh báo (Thăng)

Đề xuất: PlatformIO + Arduino framework + PubSubClient (cần nhóm chốt). Chức năng: nhận `state`/`event`, bật đèn/còi theo bảng ưu tiên, nút ACK gửi lặp lại, phát hiện mất heartbeat, hiển thị khu đang có xâm nhập.

Bản tin MQTT, bảng đèn còi, chức năng nút: `docs/mqtt.md`. Chân đèn, nút, còi, OLED: `hardware/sododaunoi_d.md`.

WiFi và mật khẩu MQTT để trong `include/secrets.h` (đã gitignore).
