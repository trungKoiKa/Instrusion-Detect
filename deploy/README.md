# deploy

- `safecam.service`: unit systemd để Pi cắm điện là `main.py` tự chạy; chết thì 5 s sau chạy lại; vòng lặp chính im quá 15 s (watchdog) thì dừng rồi chạy lại.
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

## Cài dịch vụ safecam

Cài Mosquitto, `.venv` và `.env` trước (`pi/README.md`). Dừng bản đang chạy tay (tmux) nếu có.

```bash
groups nhom17                                   # phải có video
sudo cp deploy/safecam.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now safecam             # bật ngay và tự chạy mỗi lần khởi động
systemctl status safecam --no-pager             # active (running)
sudo journalctl -u safecam -f -o short-precise  # xem log có giờ
sudo systemctl stop safecam                     # tắt hệ thống (in "Đang tắt...", không tự chạy lại)
```

- Sửa `deploy/safecam.service` thì chép lại và chạy `daemon-reload`. Sau mỗi `git pull` có đổi code: `sudo systemctl restart safecam`.
- `Type=notify`: `main.py` gửi `READY=1` sau dòng `Sẵn sàng`, gửi `WATCHDOG=1` cùng chỗ với `hb` mỗi 2 s (`pi/safecam/sdnotify.py`).
- `TimeoutStartSec=180`: Pi vừa bật thì nạp thư viện mất 65–90 s (đo trong `docs/do_dac/dich_vu.md`), mặc định 90 s quá sát.
- Không đặt `StartLimitIntervalSec`/`StartLimitBurst`: mặc định systemd chỉ bỏ cuộc khi chạy lại 5 lần trong 10 s, với `RestartSec=5` không bao giờ tới, nên dịch vụ thử lại mãi.
- Chỉ `After=mosquitto.service`, không `Requires=`: Mosquitto khởi động lại thì `main.py` tự kết nối lại, không cần chạy lại.
- Đang chạy dịch vụ thì không chạy tay `main.py` (tranh camera và cổng 8080).

WiFi của Pi phải tự vào được khi không ai đăng nhập. Nếu có lần khởi động không vào WiFi (`association took too long` rồi bỏ cuộc):

```bash
sudo nmcli connection modify Tenda_5CD458 connection.autoconnect-retries 0 802-11-wireless.powersave 2
```
