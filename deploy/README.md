# deploy

- `safecam.service`: unit systemd (Type=notify, WatchdogSec) để Pi cắm điện là tự chạy.
- `mosquitto/safecam.conf`: `listener 1883 0.0.0.0`, `allow_anonymous false`, `password_file`, `acl_file` (`persistence true` có sẵn trong file mặc định của Pi).
- `mosquitto/safecam.acl`: `safecam_pi` ghi `cam01/#`, đọc `alarm01/#`; `safecam_esp32` ngược lại; `safecam_dev` (MQTTX) đọc ghi `safecam/#`.

## Cài Mosquitto trên Pi

```bash
sudo apt install -y mosquitto mosquitto-clients
sudo cp deploy/mosquitto/safecam.conf /etc/mosquitto/conf.d/
sudo cp deploy/mosquitto/safecam.acl /etc/mosquitto/
sudo mosquitto_passwd -c /etc/mosquitto/passwd safecam_pi   # -c chỉ dùng cho tài khoản đầu tiên
sudo mosquitto_passwd /etc/mosquitto/passwd safecam_esp32
sudo mosquitto_passwd /etc/mosquitto/passwd safecam_dev
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd && sudo chmod 600 /etc/mosquitto/passwd
sudo systemctl restart mosquitto
```

Trong `conf.d/` chỉ để `safecam.conf`; file khác có `listener` hoặc `allow_anonymous true` sẽ làm hỏng cấu hình. Mật khẩu `safecam_pi` điền vào `.env` (gốc repo trên Pi), `safecam_esp32` vào `esp32/include/secrets.h`.

Kiểm tra: `mosquitto_sub -h localhost -t 'safecam/#'` phải báo `not authorised`.
