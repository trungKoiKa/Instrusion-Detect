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
| (10/11) **Rút gọn dữ liệu và train**: ~10 video ngắn có đủ điều kiện khó + 1–2 video không người; gán nhãn trên CVAT (frame step, vẽ theo vệt); chia theo video thành `train`/`val`/`test`; bỏ test_hard, test_external, trộn COCO, vòng mẫu âm khó riêng, YOLO11m gán sơ bộ, `collect_data.py` | Người dùng phản biện: quy mô đồ án không cần phức tạp. Rà bằng skill Ultralytics: chia theo video là bắt buộc (chống rò rỉ ảnh gần giống), ảnh nền giảm báo nhầm, dữ liệu nhỏ thì dùng mô hình đã học sẵn và thử `freeze=10`. Roboflow miễn phí công khai dataset nên dùng CVAT. Mất số liệu theo từng điều kiện, bù bằng hình so sánh |
| Giữ YOLO11n, không đổi sang YOLO26n | YOLO26 là mặc định cho dự án mới, nhưng YOLO11n đã đo trên Pi (7,47 FPS); đổi lúc này phải xuất và đo lại. Ghi vào hướng phát triển |
| (10/11) **Dữ liệu: 6 video × 1 phút, một ngày, `--step 5`, chia 4/1/1**; tách ảnh bằng `tools/extract_frames.py` (OpenCV) thay vì CVAT frame step; mẫu nền là vài giây đầu mỗi video | Người dùng muốn ít video và tự tách ảnh bằng Python. Đổi ánh sáng (không làm tối) và trang phục giữa các video thay cho việc quay nhiều ngày. `--step 5` cho ~2.160 ảnh, tập test lớn hơn. Giới hạn: một phòng, một ngày, test chỉ một video, ghi vào báo cáo |
| Augmentation để mặc định của Ultralytics | Ultralytics tự augment trực tuyến, chỉ trên train (sáng tối, lật ngang, phóng thu, mosaic hợp với người xa và bị che). Giữ `degrees=0`, `flipud=0` vì camera đặt ngang. Không tạo file ảnh augment |
| (17/11) **Rút gọn phạm vi đánh giá**: giữ 7 kịch bản K1, K4, K5, K7, K10, K12, K13; chạy nền 4–6 giờ thay cho 24 giờ; bỏ thí nghiệm 416 px; `freeze=10` chỉ làm nếu còn thời gian | Còn 19 ngày tới hạn nộp 06/12 mà lõi đầu-cuối chưa xong. Các kịch bản bị bỏ (K2, K3, K6, K8, K9, K11), 416 px và chạy 24 giờ ghi vào hướng phát triển |
| (17/11) **Thêm video thứ 7, quay ngày khác, chỉ dùng cho test**; chia 4/1/2, khoảng 2.520 ảnh | Tập test một video cùng ngày quá yếu để kết luận fine-tune có tác dụng. Thêm 10 phút quay và khoảng 360 ảnh gán nhãn |
| (17/11) **Thu dữ liệu bằng `tools/capture_frames.py` thay cho quay video**: tự chụp 2 ảnh/giây, 7 phiên × 110 giây (~1.540 ảnh), chia 4/1/2 theo phiên; bỏ `extract_frames.py` | Script mở camera qua `safecam.camera` nên cùng cấu hình lúc chạy thật (kể cả 50 Hz), không cần chạy `v4l2-ctl` riêng như `ffmpeg`; bỏ bước tách ảnh; ít ảnh gần trùng nên gán nhãn ít hơn. Tự chụp theo nhịp thay cho bấm phím để không chỉ có ảnh người đứng yên. Ảnh trong một phiên vẫn gần giống nhau nên vẫn phải chia theo phiên |
| (17/11) **Chia tập đã khóa**: train = s01, s02, s04, s06; val = s03; test = s05, s07 (s07 chụp 18/11 ở góc cửa sổ, ngày khác, xê dịch đồ đạc, ánh sáng bình thường). Xóa ảnh `_0001` mỗi phiên (đen do DSHOW), còn 219 ảnh/phiên | s01–s03 chụp ở góc bàn máy tính, s04–s06 ở góc cửa sổ (chỗ chạy thật, thử kịch bản, đo độ trễ); train có cả hai góc. s06 cố ý để ánh sáng yếu nên chỉ vào train, không vào val/test vì đề tài không đánh giá thiếu sáng. Test ở góc cửa sổ, có một phiên ngày khác. Ghi giới hạn: hai vị trí camera, một phiên tối chỉ dùng train |
| (17/11) **Laptop mở C270 bằng DSHOW**; video dự phòng làm theo **cách A** (hệ thống chạy thật, quay màn hình + quay ESP32 bằng điện thoại). Tùy chọn `--video` (chạy trên file video, vẫn gửi MQTT tới ESP32) để sau khi lõi đầu-cuối chạy | MSMF treo khi mở C270. Cách A không cần thêm code và thấy cả hệ thống; `--video` là tính năng mới, cần cả nhóm đồng ý. Demo trực tiếp ở phòng bảo vệ chạy `calibrate_zones.py` lại theo phòng đó |

## Giải thích đã đưa ra (để không phải hỏi lại)

- **"Xử lý trong mạng nội bộ"**: Pi chạy YOLO và broker MQTT; ESP32 nối cùng WiFi; tin nhắn chỉ đi qua router, không ra Internet. Không cần mua thêm router: dùng router sẵn có hoặc hotspot điện thoại đã tắt dữ liệu di động. Demo: rút dây WAN, `ping 8.8.8.8` báo lỗi, MQTTX vẫn thấy bản tin, đi vào khu cấm còi vẫn kêu. Nên cố định IP của Pi.
- **Broker**: Mosquitto cài trên Pi (`sudo apt install mosquitto mosquitto-clients`). MQTTX **không phải broker**, chỉ là client trên laptop để xem và gửi thử. Không dùng broker công cộng vì cần Internet. Mosquitto 2.x phải có `listener 1883 0.0.0.0`, `allow_anonymous false`, `password_file`, `persistence true`, nếu thiếu `listener` thì ESP32 không kết nối được.
- **Luồng đọc camera riêng**: camera ra 30 ảnh/s nhưng YOLO chỉ xử lý vài ảnh/s; đọc tuần tự sẽ dồn ảnh cũ, trễ dần vài giây. Luồng riêng gọi `grab()` liên tục, chỉ giữ ảnh mới nhất, chỉ `retrieve()` (giải nén) khi YOLO cần. `grab()` và `retrieve()` phải gọi **cùng một luồng**. Mỗi ảnh có số thứ tự để không xử lý lại. Chỉ module camera được mở camera.
- **Tên thiết bị**: mở theo `/dev/v4l/by-id/...-video-index0` thay vì `/dev/video0` (số có thể đổi khi cắm lại). C270 quên cấu hình khi rút cắm, nên áp lại mỗi lần mở.

## Còn chờ / việc tiếp theo

- Đo thực tế góc nhìn C270 ở vị trí đặt (phép thử: đứng ở mép gần nhất của khu cấm, xem có thấy cả người không).
- Bước 1: `pi/safecam/camera.py` + `detector.py`, chạy YOLO11n NCNN imgsz 320 trên Pi, đo FPS 30–60 phút. Mốc 03/11.
- ESP32 dùng PlatformIO + Arduino + PubSubClient: chờ Thăng chốt.
