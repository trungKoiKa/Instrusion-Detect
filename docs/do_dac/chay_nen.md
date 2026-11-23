# Chạy nền đếm báo động giả

Chạy 23/11/2026 tối, mô hình gốc YOLO11n NCNN 320 px. Mục đích: đếm số báo động giả mỗi giờ khi hệ thống chạy liên tục (chỉ tiêu ở mục 1 bản đề xuất) và xem chạy lâu có treo, mất kết nối, nóng hay hạ xung không.

## Cách làm

- `main.py` chạy trong `tmux`, log thêm giờ ở đầu mỗi dòng và lưu ra `~/chay_nen_2311.log` trên Pi:
  `python -u -m safecam.main 2>&1 | while IFS= read -r l; do echo "$(date '+%F %T') $l"; done | tee -a ~/chay_nen_2311.log`
- Một `tmux` khác ghi `vcgencmd measure_temp` và `vcgencmd get_throttled` mỗi phút vào `~/nhiet_do_2311.log`.
- Phòng bật đèn, sinh hoạt bình thường, người trực ngồi gần ESP32: còi kêu thì xem ai đang ở khu cấm rồi bấm nút.
- Đếm sự kiện bằng `next_id` trong `state.json` lúc bắt đầu và lúc dừng, đối chiếu từng mã với log. Sự kiện có người thật trong khu cấm thì không tính là báo giả.
- Thông số (tạm, chưa chọn trên val): `conf` 0,25, T = 2 s, K_min = 5, p = 0,5, `n_min` 8, `lost_after_s` 5 s, `detail_min` 25. Khu cấm 2, 3.
- Giờ theo Pi, đã đồng bộ NTP (`System clock synchronized: yes`).

## Kết quả

| Mục | Kết quả |
| --- | --- |
| Thời gian chạy liên tục | 23/11 19:15:15 → 24/11 01:39:50, **6 giờ 24 phút (6,4 giờ)** |
| Bộ đếm | `intr.next_id` 22 → 24, `obs.next_id` 10 → 10 |
| Sự kiện xâm nhập | 2 (I22, I23), cả hai có người thật trong khu 3 |
| **Báo động giả** | **0 lần (0 lần/giờ)** |
| Thấy người nhưng chưa đủ bằng chứng (`suspected` → `none` sau ~2 s, không báo) | 3 lần: 19:31:36, 20:11:20, 20:20:13 |
| Cảnh báo quan sát | 0. Một lần `suspect` 1 s lúc 22:24:03 rồi `ok` |
| Ảnh hỏng (`Corrupt JPEG data`) | 1 lần lúc 19:32:13, chương trình chạy tiếp |
| MQTT | Không mất kết nối lần nào |
| Treo, tự dừng | Không |
| Nhiệt độ CPU | Cao nhất 48,7 °C (19:43), lúc dừng 45,7 °C |
| Hạ xung | Không (`throttled=0x0` suốt buổi) |

| Mã | Báo động | Khu | ACK | Nguyên nhân |
| --- | --- | --- | --- | --- |
| I22 | 19:15:18 | 3 | 19:15:27 | Người thật trong khu 3 lúc chương trình vừa khởi động |
| I23 | 19:33:01 | 3 | 19:33:10 | Người thật (Trung Anh) đi vào khu 3 |

## Giới hạn (ghi vào báo cáo)

- Một lần chạy, một buổi tối, một phòng, ít người qua lại.
- 0 lần trong 6,4 giờ không có nghĩa là tỷ lệ báo giả bằng 0. Theo quy tắc "ba chia n", với độ tin cậy 95% thì tỷ lệ thật không quá khoảng 3 / 6,4 ≈ 0,47 lần/giờ.
- Nguyên nhân từng sự kiện dựa vào lời người trực, chưa có ảnh bằng chứng (chưa làm phần lưu ảnh khi cảnh báo).
