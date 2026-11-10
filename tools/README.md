# tools

- `extract_frames.py`: tách ảnh từ video để gán nhãn, `--step N` lấy 1 ảnh mỗi N khung (mặc định 1 = toàn bộ; dùng 5). Tên ảnh `<video>_<khung>.jpg`.
- `calibrate_zones.py`: chụp ảnh, click ranh giới khu, ghi `config/zones.yaml`.
- `bench_pi.py`: đo FPS, CPU, RAM, nhiệt độ, `get_throttled` trong 30–60 phút.
- `latency_led.py`: đo độ trễ camera bằng LED GPIO.
