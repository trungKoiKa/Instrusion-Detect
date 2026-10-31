# config

Cấu hình dùng chung cho chương trình chính và script thu dữ liệu (mục 3 của đề xuất).

- `camera.yaml`: đường dẫn `/dev/v4l/by-id/...`, MJPG 640×480 30 fps, 50 Hz, cân bằng trắng.
- `zones.yaml`: 3 tọa độ x chia 4 khu, cờ `forbidden` của từng khu.
- `detection.yaml`: ngưỡng tin cậy, T, K_min, p, n_min.
- `mqtt.yaml`: địa chỉ broker, tên topic, tài khoản (mật khẩu để trong `.env`, không commit).
