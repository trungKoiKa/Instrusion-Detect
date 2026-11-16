# tools

- `capture_frames.py`: tự chụp ảnh từ C270 để gán nhãn, `--session s01` (mỗi lần chạy một phiên), mặc định 110 giây × 2 ảnh/giây. Ảnh lưu `data/raw/<phiên>/<phiên>_0001.jpg`; không ghi đè phiên đã có.
- `calibrate_zones.py`: chụp ảnh, click ranh giới khu, ghi `config/zones.yaml`.
- `bench_pi.py`: đo FPS, CPU, RAM, nhiệt độ, `get_throttled` trong 30–60 phút.
- `latency_led.py`: đo độ trễ camera bằng LED GPIO.
