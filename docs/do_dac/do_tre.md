# Đo độ trễ cảnh báo

Đo 24/11/2026 chiều, mô hình gốc YOLO11n NCNN 320 px. Mục đích: đo thời gian từ lúc người bước vào khu cấm tới lúc ESP32 báo động (chỉ tiêu PCN1: 95% số lần dưới 2 s), và kiểm tra cái giá của luật cửa sổ T giây (chờ đủ bằng chứng để chống báo giả thì báo chậm hơn).

## Cách làm

- Dán băng dính dọc trên tường ở cột x = 320 (ranh giới khu 1 và khu 2), kiểm tra bằng ảnh chụp từ C270 (`tools/capture_frames.py`) mở bằng Paint.
- Điện thoại đặt cố định sát C270, cùng hướng nhìn, quay **video thường 30 fps**; khung hình thấy băng dính, đường đi và đèn đỏ ESP32. Quay một video liền cho nhiều lượt.
- Mỗi lượt: đứng ở khu 1, đi bình thường sang khu 2, đèn đỏ sáng thì bấm ACK, rời khu, chờ đèn xanh thêm 5 s rồi làm lượt sau.
- Đọc video từng khung bằng Avidemux:
  - tA: khung đầu tiên đường giữa thân người (giữa hai vai) đã qua băng dính. Pi xét khu theo tâm ngang khung người nên lấy giữa thân, không lấy tay chân.
  - tB: khung đầu tiên đèn đỏ sáng.
  - Độ trễ = tB − tA. Sai số mỗi lượt khoảng ±0,07 s (lệch tối đa 1 khung 1/30 s ở mỗi đầu).
- Thông số (tạm, chưa chọn trên val): `conf` 0,25, T = 2 s, K_min = 5, p = 0,5, `n_min` 8. Khu cấm 2, 3.
- Log `main.py` có giờ (`~/do_tre_2411.log`) để kiểm tra mỗi lượt đều có báo động và ACK.

## Kết quả

Buổi thử có nhiều lượt hơn, nhưng chỉ 8 lượt có video quay đúng nên chỉ dùng 8 lượt này.

| Lượt | tA | tB | Độ trễ (s) |
| --- | --- | --- | --- |
| 1 | 0:15,335 | 0:16,301 | 0,97 |
| 2 | 0:29,003 | 0:30,470 | 1,47 |
| 3 | 0:41,470 | 0:42,969 | 1,50 |
| 4 | 0:52,904 | 0:53,805 | 0,90 |
| 5 | 1:06,873 | 1:07,540 | 0,67 |
| 6 | 1:21,908 | 1:24,208 | 2,30 |
| 7 | 1:33,008 | 1:34,234 | 1,23 |
| 8 | 1:48,909 | 1:50,376 | 1,47 |

| Chỉ số | Giá trị |
| --- | --- |
| Trung bình ± độ lệch chuẩn | **1,31 ± 0,50 s** |
| Trung vị | 1,35 s |
| Nhỏ nhất / lớn nhất | 0,67 s / 2,30 s |
| Số lượt dưới 2 s | **7/8 (87,5%)** |
| Bỏ sót (đi vào khu mà không báo) | 0 |

## So với ước tính lý thuyết

| Phần | Ước tính | Ghi chú |
| --- | --- | --- |
| Camera chụp, nén MJPG, USB, luồng đọc | 0,1–0,2 s | Giả định |
| Chờ ảnh đầu tiên có người và YOLO xử lý | 0,13–0,27 s | 7,47 FPS đo trên Pi |
| Luật cửa sổ: đủ 50% ảnh thấy người trong T = 2 s | ~1,0 s | ≈ p × T; K_min = 5 chỉ cần ~0,67 s nên p quyết định |
| MQTT nội bộ, ESP32 nhận bản tin | 0,01–0,05 s | |
| **Tới lúc còi kêu** | **1,2–1,5 s** | Còi bật ngay khi nhận `state` |
| Đèn đỏ | thêm 0–0,5 s | Đèn nháy theo đồng hồ ESP32 (0,5 s sáng, 0,5 s tắt), bản tin tới lúc nửa tắt thì phải chờ |

Trung bình đo được 1,31 s nằm trong khoảng ước tính, nên không khâu nào chậm bất thường. Phần lớn độ trễ do luật cửa sổ (cấu hình) quyết định, không do tốc độ mô hình.

- Lượt 6 (2,30 s): có thể do đèn rơi vào nửa tắt (còi có thể chỉ ~1,8 s) hoặc YOLO bỏ sót vài ảnh lúc người đang đi.
- Lượt 5 (0,67 s) nhanh hơn mức ~1 s: có thể tâm khung người đã sang khu 2 trước khi giữa thân qua băng dính (tay chân vung, đứng sát vạch), nên cửa sổ đã có sẵn vài ảnh có người.

## Kết luận về PCN1

Trung bình 1,31 s, 7/8 lượt dưới 2 s. Với 8 lượt, muốn nói "95% dưới 2 s" thì cả 8 lượt phải dưới 2 s, nên **chưa chứng minh được PCN1**. Số đo theo đèn là cận trên của độ trễ tới còi.

## Giới hạn (ghi vào báo cáo)

- Chỉ 8 lượt (ít hơn 10–15 lượt dự kiến), một buổi, một phòng, một người, đi cùng một hướng từ khu 1 sang khu 2.
- Đo tới đèn, không đo được còi trên video; đèn nháy làm số đo dài thêm tới 0,5 s. Nhóm chốt không sửa firmware để đèn sáng ngay.
- tA chọn bằng mắt theo giữa thân người, có thể lệch với tâm khung người mà YOLO tính.
- Ở môi trường khác (xa hơn, bị che, ánh sáng khác) mô hình bỏ sót nhiều ảnh hơn thì cần thêm ảnh mới đủ 50%, nên độ trễ tăng; cần đo lại tại chỗ triển khai. Tăng T hoặc p để giảm báo giả cũng làm độ trễ tăng (≈ p × T).
- [cần bổ sung: khoảng cách từ người tới camera lúc thử]
