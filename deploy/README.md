# deploy

- `safecam.service`: unit systemd (Type=notify, WatchdogSec) để Pi cắm điện là tự chạy.
- `mosquitto/safecam.conf`: `listener 1883 0.0.0.0`, `allow_anonymous false`, `password_file`, `persistence true`, ACL.
