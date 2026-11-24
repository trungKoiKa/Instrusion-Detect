# Mục lục báo cáo ĐATN (tạm chốt 24/11/2026)

Theo đề cương đã duyệt: 3 chương + Kết luận. Người viết theo bảng phân công của đề cương (Phụ lục 1): **A** = Hoàng Trung Anh, **T** = Nguyễn Nhật Thăng. Cấu trúc học theo quyển mẫu nhóm 06, nhưng bỏ phần app/web/cơ sở dữ liệu, dành chỗ cho dữ liệu, fine-tune và số đo.

Nội dung tối thiểu 70 trang: chương 1 khoảng 15, chương 2 khoảng 28, chương 3 khoảng 25, phần cuối khoảng 5. Xưng "nhóm" suốt bài.

## Phần đầu (đánh số La Mã)

Bìa · Trang lót · Đề cương · Bảng phân công công việc · Lời cảm ơn · Mục lục · Danh mục ký hiệu và chữ viết tắt · Danh mục hình · Danh mục bảng

**Lời mở đầu** (A + T, bắt đầu số Ả Rập): lý do chọn đề tài, mục tiêu kèm chỉ tiêu (bảng mục 1 bản đề xuất), phạm vi (làm / không làm), ba điểm bổ sung so với đề cương (fine-tune, đo hiệu năng trên Pi, giám sát camera), bố cục 3 chương.

## CHƯƠNG 1: TỔNG QUAN VỀ KIẾN TRÚC IoT, HỌC MÁY VÀ NỀN TẢNG RASPBERRY PI VÀ ESP32

- 1.1 Bài toán giám sát phát hiện người xâm nhập (A + T)
  - 1.1.1 Nhu cầu và hạn chế của camera giám sát truyền thống
  - 1.1.2 Các giải pháp hiện có: cảm biến PIR, camera có người trực, camera AI trên cloud, AI tại biên (bảng so sánh)
- 1.2 Kiến trúc IoT và xử lý tại biên (T)
  - 1.2.1 Kiến trúc IoT nhiều lớp
  - 1.2.2 Điện toán đám mây và xử lý tại biên
- 1.3 Giao thức MQTT (T)
  - 1.3.1 Mô hình publish/subscribe và broker
  - 1.3.2 QoS, retain, LWT, keep-alive
  - 1.3.3 So sánh MQTT với HTTP và CoAP
- 1.4 Học máy, học sâu và bài toán phát hiện đối tượng (A)
  - 1.4.1 Học máy và học sâu
  - 1.4.2 Mạng nơ-ron tích chập
  - 1.4.3 Bài toán phát hiện đối tượng và chỉ số đánh giá (IoU, precision, recall, mAP)
  - 1.4.4 Học chuyển giao và tinh chỉnh mô hình
- 1.5 Mô hình YOLO (A)
  - 1.5.1 Nguyên lý phát hiện một giai đoạn
  - 1.5.2 YOLO11 và lý do chọn bản n
  - 1.5.3 Triển khai trên thiết bị biên: định dạng NCNN
- 1.6 Nền tảng phần cứng (A)
  - 1.6.1 Raspberry Pi 4
  - 1.6.2 ESP32
  - 1.6.3 Camera USB Logitech C270
  - 1.6.4 Vai trò từng thiết bị trong hệ thống
- 1.7 Kết luận chương 1

## CHƯƠNG 2: XÂY DỰNG HỆ THỐNG HỌC SÂU GIÁM SÁT PHÁT HIỆN NGƯỜI XÂM NHẬP VÀ CẢNH BÁO TRÊN NỀN TẢNG RASPBERRY PI VÀ ESP32

- 2.1 Phân tích yêu cầu (A)
  - 2.1.1 Kịch bản sử dụng và tác nhân
  - 2.1.2 Yêu cầu chức năng
  - 2.1.3 Yêu cầu phi chức năng (bảng chỉ tiêu, mỗi dòng có cột "cách kiểm chứng")
- 2.2 Kiến trúc tổng thể (A)
  - 2.2.1 Sơ đồ khối và các thành phần
  - 2.2.2 Luồng dữ liệu: phát hiện → cảnh báo, ACK, heartbeat
  - 2.2.3 Lựa chọn công nghệ (bảng có cột phương án thay thế và lý do)
- 2.3 Thu ảnh và phát hiện người trên Raspberry Pi (A)
  - 2.3.1 Luồng đọc camera và cấu hình camera
  - 2.3.2 Mô-đun phát hiện YOLO11n NCNN 320 px
  - 2.3.3 Vùng quan tâm (ROI) dạng 4 khu dọc: lý do chọn, giới hạn
  - 2.3.4 Điều kiện xác định xâm nhập theo cửa sổ T giây (K_min, p, n_min) và tạo sự kiện
  - 2.3.5 Luồng hình theo dõi trên máy tính (`stream.py`, MJPEG)
- 2.4 Dữ liệu và quy trình tinh chỉnh mô hình (A)
  - 2.4.1 Các điều kiện quan sát khó cần cải thiện
  - 2.4.2 Thu thập dữ liệu theo phiên
  - 2.4.3 Gán nhãn và chia tập theo phiên
  - 2.4.4 Cấu hình huấn luyện và phương pháp đánh giá
- 2.5 Quản lý trạng thái sự kiện (T)
  - 2.5.1 Hai trạng thái độc lập: xâm nhập và quan sát camera
  - 2.5.2 Máy trạng thái xâm nhập
  - 2.5.3 Máy trạng thái quan sát camera (mất hình, bị che, Pi quá chậm)
  - 2.5.4 Quy tắc xác nhận (ACK) và bảng ưu tiên đèn, còi
  - 2.5.5 Lưu trạng thái và khôi phục sau khởi động lại
- 2.6 Thiết kế giao tiếp MQTT (T)
  - 2.6.1 Broker Mosquitto cục bộ, tài khoản và ACL
  - 2.6.2 Danh sách topic
  - 2.6.3 Cấu trúc bản tin state, event, hb, ack
  - 2.6.4 Cơ chế ACK gửi lặp, heartbeat, LWT
  - 2.6.5 Xử lý mất kết nối và kết nối lại
- 2.7 Thiết kế trạm cảnh báo ESP32 (T)
  - 2.7.1 Sơ đồ nguyên lý và đấu nối: đèn, còi qua transistor, nút
  - 2.7.2 Bảng linh kiện và phân bố chân
  - 2.7.3 Lưu đồ firmware
- 2.8 Kết luận chương 2

## CHƯƠNG 3: TRIỂN KHAI VÀ ĐÁNH GIÁ HOẠT ĐỘNG HỆ THỐNG

Cột "Bằng chứng" cho biết đã có gì trong repo (24/11) và còn thiếu gì.

| Mục | Người viết | Bằng chứng |
| --- | --- | --- |
| 3.1 Mô hình thực nghiệm: bố trí hiện trường, vạch khu, phần cứng, phần mềm | A + T | Cấu hình trong `config/`. **Thiếu:** ảnh hiện trường, ảnh bo ESP32 |
| 3.2 Triển khai trên Raspberry Pi: chương trình chính, đo hiệu năng (FPS, CPU, RAM, nhiệt độ, hạ xung) | A | `logs/bench_20261031_235817.csv` (45 phút, YOLO riêng, OpenCV 5.0) và biểu đồ PNG; nhiệt độ lúc chạy nền 6,4 giờ; 3.2.3 FPS `main.py` khi bật/tắt stream (`docs/do_dac/stream_fps.md`) |
| 3.3 Huấn luyện và đánh giá mô hình: tập dữ liệu, kết quả 3 seed, so sánh gốc và fine-tune trên test, ảnh so sánh, phân tích lỗi | A | Kết quả trên val (18/11) trong `tom_tat_trao_doi.md`. **Thiếu:** phiên s07, kết quả trên test, notebook trong `ml/notebooks/` |
| 3.4 Triển khai broker và trạm cảnh báo ESP32, bản tin MQTT thực tế | T | `deploy/mosquitto/`, `esp32/src/main.cpp`, `docs/mqtt.md`. **Thiếu:** ảnh chụp log MQTTX hoặc `mosquitto_sub` |
| 3.5.1 Tham số dùng trong thử nghiệm | A | Đã viết (nhóm chốt 25/11): giữ tham số tạm T = 2 s, K_min = 5, p = 0,5, n_min = 8, conf = 0,25, vì ảnh val 2 ảnh/giây không mô phỏng đúng Pi ~8 FPS; chọn trên val chuyển sang hướng phát triển |
| 3.5.2 Độ trễ cảnh báo | A | `docs/do_dac/do_tre.md`: 8 lượt, video 30 fps, trung bình 1,31 s, 7/8 dưới 2 s. **Thiếu:** khoảng cách người tới camera |
| 3.5.3 Chạy liên tục và báo động giả | A | `docs/do_dac/chay_nen.md`: 6,4 giờ, 0 báo động giả |
| 3.5.4 Kịch bản sự cố K1, K4, K5, K7, K10, K12, K13 | T | `docs/kich_ban_su_co.md`: 8/8 lần đạt |
| 3.6 Đánh giá chung, hạn chế và hướng phát triển (bảng yêu cầu / kết quả đo / đạt hay không) | A + T | Lấy từ 3.2–3.5 |
| 3.7 Kết luận chương 3 | A + T | |

## Phần cuối

- **Kết luận** (A + T): một đoạn, không thêm thông tin mới.
- **Trách nhiệm đạo đức nghề nghiệp** (A + T): quyền riêng tư dữ liệu hình ảnh, giấy đồng ý của người được chụp, làm mờ mặt, Luật 91/2025/QH15, Nghị định 356/2025/NĐ-CP (đối chiếu bản gốc trước khi trích), báo động giả và bỏ sót, an toàn điện.
- **Tài liệu tham khảo**: chỉ 5 tài liệu trong đề cương, ký hiệu [1]–[5]. Phần YOLO, MQTT, NCNN vẫn viết đầy đủ nhưng không trích (`bao_cao/tai_lieu_tham_khao.md`).
- **Phụ lục** (nếu cần): bản tin MQTT đầy đủ, file cấu hình.

## Giới hạn phải ghi trong báo cáo

- Mọi thử nghiệm trên phần cứng (kịch bản sự cố, chạy nền) dùng **mô hình gốc**, chưa dùng mô hình fine-tune.
- 4 khu dọc là hướng nhìn từ camera, không phải ô trên sàn.
- Mỗi kịch bản sự cố thử 1 lần (K7 2 lần), chưa có thống kê.
- Chạy nền một buổi tối, ít người qua lại: 0 lần trong 6,4 giờ chỉ cho biết tỷ lệ báo giả thật không quá khoảng 0,47 lần/giờ (độ tin cậy 95%).
- Dữ liệu chụp trong một phòng, hai vị trí camera; tập test chỉ có hai phiên.
- Độ trễ đo 8 lượt, một người, một hướng đi, đo tới đèn (cận trên của còi): chưa chứng minh được 95% dưới 2 s.
- Số đo hiệu năng ngày 31/10 chỉ chạy YOLO, chưa chạy đủ mọi thành phần, và dùng OpenCV 5.0 (bản hiện đã chặn). Khi chạy đủ thành phần chỉ có FPS của `main.py` (`stream_fps.md`, mỗi trường hợp một lần 5 phút).
- Tham số cửa sổ chọn theo kinh nghiệm, không chọn trên val.
- Chưa có `safecam.service` (tự chạy khi cắm điện, watchdog), chưa có ảnh bằng chứng và log ghi vòng: không viết như đã làm.
