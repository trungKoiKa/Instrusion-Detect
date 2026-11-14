# config

Cấu hình của chương trình chính (mục 3 của đề xuất). Lúc quay dữ liệu bằng `ffmpeg` cũng dùng đúng cấu hình camera trong `camera.yaml`.

- `camera.yaml`: đường dẫn `/dev/v4l/by-id/...`, MJPG 640×480 30 fps, 50 Hz, cân bằng trắng.
- `zones.yaml`: 3 tọa độ x chia 4 khu, cờ `forbidden` của từng khu.
- `detection.yaml`: ngưỡng tin cậy, T, K_min, p, n_min.
- `mqtt.yaml`: địa chỉ broker, tên topic, tài khoản (mật khẩu để trong `.env`, không commit).
