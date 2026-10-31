# Tóm tắt trao đổi với Claude (31/10/2026)

Các câu hỏi đã hỏi, câu trả lời đã thống nhất và lý do. Đọc kèm `CLAUDE.md` và bản đề xuất _12.

## Quyết định và lý do

| Quyết định | Lý do |
| --- | --- |
| Chia khung hình thành **4 khu dọc**, xét theo tâm ngang bbox; file cấu hình chọn khu cấm (ví dụ khu 2, 3) | Camera chưa nghiêng xuống được, đặt ngang ở ~1,6 m. Theo ước tính từ góc nhìn C270 (~55° chéo), camera đặt ngang chỉ thấy sàn từ ~5 m trở ra (chưa đo thực tế), nên cách "điểm chân trong ROI đa giác" sai với người ở gần. Một dải dọc = một hướng nhìn, không phải ô trên sàn: ghi rõ là giới hạn |
| Vẫn chỉ **một** sự kiện xâm nhập, bản tin mang `zones: [2, 3]`; mỗi khu có cửa sổ T giây riêng | Không phình máy trạng thái; người đi lướt qua ranh giới không bị cộng dồn sai |
| **Bỏ chế độ canh gác (arm/disarm)**: chương trình chạy là canh gác, muốn tắt thì `systemctl stop` | Người dùng chưa cần. Arm/disarm chỉ là phần mềm trên Pi, không cần thêm phần cứng (chỉ cần RTC DS3231 nếu làm lịch giờ). Để ở phần mở rộng |
| **Bỏ thiếu sáng**; fine-tune cho **người xa, bị che một phần (sau bàn ghế), góc nhìn lạ, cúi/ngồi** | Người dùng muốn thêm dữ liệu điều kiện khó, không phải tối. Vì vậy bỏ luôn phần chặn trần phơi sáng; camera để phơi sáng tự động, chỉ cố định MJPG 640×480 30 fps, 50 Hz, cân bằng trắng |
| Bản đề xuất rút từ ~12.800 xuống ~2.600 từ | Bản dài khó hiểu. **Tài liệu phải ngắn, dễ hiểu**; chi tiết cài đặt để trong code/README |
| Git: mỗi phần một nhánh + một PR, commit tới đâu đẩy tới đó, **không xóa nhánh**, **không dòng Co-Authored-By: Claude** | Đồ án cần giữ lịch sử và đứng tên người làm |

## Giải thích đã đưa ra (để không phải hỏi lại)

- **"Xử lý trong mạng nội bộ"**: Pi chạy YOLO và broker MQTT; ESP32 nối cùng WiFi; tin nhắn chỉ đi qua router, không ra Internet. Không cần mua thêm router: dùng router sẵn có hoặc hotspot điện thoại đã tắt dữ liệu di động. Demo: rút dây WAN, `ping 8.8.8.8` báo lỗi, MQTTX vẫn thấy bản tin, đi vào khu cấm còi vẫn kêu. Nên cố định IP của Pi.
- **Broker**: Mosquitto cài trên Pi (`sudo apt install mosquitto mosquitto-clients`). MQTTX **không phải broker**, chỉ là client trên laptop để xem và gửi thử. Không dùng broker công cộng vì cần Internet. Mosquitto 2.x phải có `listener 1883 0.0.0.0`, `allow_anonymous false`, `password_file`, `persistence true`, nếu thiếu `listener` thì ESP32 không kết nối được.
- **Luồng đọc camera riêng**: camera ra 30 ảnh/s nhưng YOLO chỉ xử lý vài ảnh/s; đọc tuần tự sẽ dồn ảnh cũ, trễ dần vài giây. Luồng riêng gọi `grab()` liên tục, chỉ giữ ảnh mới nhất, chỉ `retrieve()` (giải nén) khi YOLO cần. `grab()` và `retrieve()` phải gọi **cùng một luồng**. Mỗi ảnh có số thứ tự để không xử lý lại. Chỉ module camera được mở camera.
- **Tên thiết bị**: mở theo `/dev/v4l/by-id/...-video-index0` thay vì `/dev/video0` (số có thể đổi khi cắm lại). C270 quên cấu hình khi rút cắm, nên áp lại mỗi lần mở.

## Còn chờ / việc tiếp theo

- Đo thực tế góc nhìn C270 ở vị trí đặt (phép thử: đứng ở mép gần nhất của khu cấm, xem có thấy cả người không).
- Bước 1: `pi/safecam/camera.py` + `detector.py`, chạy YOLO11n NCNN imgsz 320 trên Pi, đo FPS 30–60 phút. Mốc 03/11.
- ESP32 dùng PlatformIO + Arduino + PubSubClient: chờ Thăng chốt.
