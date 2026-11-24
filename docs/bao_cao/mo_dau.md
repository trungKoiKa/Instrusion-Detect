# LỜI MỞ ĐẦU

Camera giám sát ngày càng phổ biến ở nhà ở, cửa hàng và kho bãi, nhưng phần lớn chỉ làm nhiệm vụ ghi hình. Việc phát hiện có người đi vào nơi không được phép vẫn dựa vào người ngồi xem màn hình, hoặc chỉ được biết khi xem lại đoạn ghi sau khi sự việc đã xảy ra. Các camera thông minh trên thị trường tự động hóa việc này bằng cách gửi hình ảnh lên máy chủ đám mây để phân tích. Đổi lại, hệ thống ngừng cảnh báo khi mất Internet, và hình ảnh bên trong nhà phải đi ra ngoài.

Trong vài năm gần đây, các mô hình phát hiện đối tượng cỡ nhỏ như YOLO đã đủ nhẹ để chạy trên máy tính nhúng giá rẻ như Raspberry Pi. Nhờ đó có thể đặt toàn bộ việc phát hiện ngay cạnh camera và truyền cảnh báo trong mạng nội bộ. Nhóm chọn đề tài này để xây dựng một hệ thống như vậy hoàn chỉnh từ camera tới còi báo động, chạy trên phần cứng thật, và đo xem hệ thống hoạt động tốt tới đâu thay vì chỉ dừng ở mức chạy thử mô hình. Đề tài cũng cho phép nhóm vận dụng cùng lúc các kiến thức về IoT, giao thức MQTT, học sâu và lập trình nhúng.

**Mục tiêu của đồ án.** Nhóm xây dựng một hệ thống giám sát trong đó camera quan sát khu vực cần bảo vệ. Khi có người đi vào khu cấm, Raspberry Pi 4 phát hiện bằng mô hình YOLO11n rồi gửi cảnh báo qua giao thức MQTT tới một trạm báo động dùng ESP32 đặt ở bàn người trực. Trạm bật đèn và còi cho tới khi người trực bấm nút xác nhận. Toàn bộ hệ thống chạy trong mạng WiFi nội bộ, không cần Internet. Hệ thống phải đạt các chỉ tiêu đo được sau:

- Độ trễ từ lúc người bước vào khu cấm tới lúc còi kêu dưới 2 giây ở 95% số lần thử.
- Sau khi tinh chỉnh, mô hình phát hiện người tốt hơn ở các điều kiện quan sát khó, trong khi cảnh bình thường không kém đi.
- Đo được số lần báo động giả mỗi giờ khi hệ thống chạy liên tục.
- Xử lý đúng 7 kịch bản sự cố như che camera, mất mạng, khởi động lại Raspberry Pi, mất điện.

Danh sách đầy đủ các yêu cầu và cách kiểm chứng từng yêu cầu được trình bày ở mục 2.1.

**Nội dung bổ sung so với đề cương.** Trong quá trình thực hiện, nhóm bổ sung ba nội dung:

1. Tinh chỉnh mô hình YOLO11n bằng dữ liệu tự chụp tại nơi lắp đặt, cho các điều kiện quan sát khó: người ở xa, người bị bàn ghế che một phần, người đi sát mép khung hình hoặc quay lưng, người cúi hoặc ngồi.
2. Đo hiệu năng thực tế của YOLO11n định dạng NCNN, ảnh đầu vào 320 điểm ảnh, trên Raspberry Pi 4: số ảnh xử lý mỗi giây, mức dùng CPU và RAM, nhiệt độ, hiện tượng hạ xung.
3. Giám sát khả năng quan sát của camera: hệ thống phát hiện khi mất hình, khi camera bị che hoặc khi Raspberry Pi xử lý quá chậm, và trạm ESP32 tự báo khi không còn nhận được tín hiệu từ Raspberry Pi. Nguyên tắc xuyên suốt là khung hình không nhìn được thì không bao giờ được coi là không có người.

**Phạm vi.** Hệ thống dùng một camera đặt ngang ở độ cao khoảng 1,6 m. Khung hình được chia thành 4 khu dọc, khu nào là khu cấm do file cấu hình quy định. Hệ thống hoạt động trong nhà, đủ ánh sáng, với một router WiFi nội bộ, và luôn ở chế độ canh gác khi chương trình đang chạy. Đồ án không giải quyết các trường hợp thiếu sáng hoặc ban đêm, không nhận diện khuôn mặt hay hành động, không xây dựng giao diện web hay lưu trữ trên đám mây.

**Phương pháp thực hiện.** Nhóm kết hợp nghiên cứu tài liệu, thiết kế và thực nghiệm trên phần cứng thật. Chương trình trên Raspberry Pi viết bằng Python, chia thành các mô-đun có kiểm thử tự động chạy được trên máy tính mà không cần phần cứng. Firmware ESP32 viết trên Arduino framework. Dữ liệu ảnh được chụp tại nơi lắp đặt, gán nhãn trên CVAT, chia tập theo phiên chụp và huấn luyện trên Google Colab. Hệ thống được đánh giá bằng đo hiệu năng trên Pi, chạy liên tục nhiều giờ, đo độ trễ cảnh báo và thử các kịch bản sự cố.

**Bố cục của báo cáo.** Ngoài Lời mở đầu và Kết luận, báo cáo gồm ba chương:

- **Chương 1: Tổng quan về kiến trúc IoT, học máy và nền tảng Raspberry Pi và ESP32.** Chương này trình bày bài toán phát hiện người xâm nhập và các giải pháp hiện có, kiến trúc IoT và xử lý tại biên, giao thức MQTT, học sâu và bài toán phát hiện đối tượng, mô hình YOLO và ba thiết bị phần cứng chính.
- **Chương 2: Xây dựng hệ thống học sâu giám sát phát hiện người xâm nhập và cảnh báo trên nền tảng Raspberry Pi và ESP32.** Chương này phân tích yêu cầu và trình bày thiết kế từng khối: phát hiện người trên Raspberry Pi, dữ liệu và quy trình tinh chỉnh mô hình, quản lý trạng thái sự kiện, giao tiếp MQTT và trạm cảnh báo ESP32.
- **Chương 3: Triển khai và đánh giá hoạt động hệ thống.** Chương này trình bày việc triển khai trên phần cứng thật và các kết quả đo: hiệu năng trên Raspberry Pi, kết quả tinh chỉnh mô hình, độ trễ cảnh báo, báo động giả khi chạy liên tục, kết quả thử các kịch bản sự cố, và đối chiếu với các chỉ tiêu đã đặt ra.
