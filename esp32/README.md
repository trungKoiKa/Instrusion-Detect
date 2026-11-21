# esp32 – firmware trạm cảnh báo (Thăng)

PlatformIO + Arduino + PubSubClient + ArduinoJson. Chức năng: kết nối MQTT có LWT (`safecam/alarm01/status`), bật đèn/còi theo `state` của Pi, mất 3 nhịp `hb` (6 giây) thì đỏ vàng xen kẽ và bíp ngắn (đang cảnh báo xâm nhập thì giữ đỏ nháy và còi), 4 nút cùng là ACK: tắt còi tại chỗ, gửi ACK mỗi giây tới khi thấy mã trong `acked`, mất mạng thì nhớ ACK và gửi khi có mạng lại (K5).

Bản tin MQTT, bảng đèn còi: `docs/mqtt.md`. Chân đèn, nút, còi: `hardware/sododaunoi_d.md`.

## Cấu hình

Chép `include/secrets.h.example` thành `include/secrets.h` (đã gitignore), điền tên và mật khẩu WiFi 2,4 GHz, IP cố định của Pi, mật khẩu tài khoản `safecam_esp32`.

## Nạp code

Bo nạp qua header P1 (TX0, RX0, GND), không có DTR/RTS nên không tự vào chế độ nạp. Cấp nguồn qua jack DC, nối mạch USB–UART chéo TX↔RX.

1. Tắt Serial Monitor (nó giữ cổng COM).
2. Giữ FLASH, bấm và thả RESET, thả FLASH.
3. Trong thư mục `esp32`: `pio run -t upload`.
4. Bấm RESET để chạy code mới; xem log: `pio device monitor`.

Mới khởi động, chưa có `hb` thì bo báo mất Pi vài giây: đúng thiết kế, không báo "bình thường" khi chưa nghe thấy Pi.
