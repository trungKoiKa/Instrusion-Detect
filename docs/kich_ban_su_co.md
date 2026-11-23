# Kịch bản thử sự cố (K1, K4, K5, K7, K10, K12, K13)

Soạn 23/11/2026 theo code trên `main` sau PR #41. Nhóm chốt 23/11: **mỗi kịch bản thử 1 lần trên phần cứng thật**, riêng K7 thử 2 lần (Ctrl+C và `sudo reboot`). Các nhánh phụ không thử trên phần cứng (ghi ở từng kịch bản) đã kiểm bằng giả lập vòng lặp `main.py` trên laptop hoặc test tự động trong `pi/tests/`.

Mỗi lần thử ghi một dòng vào bảng kết quả, kèm **mã sự kiện đọc từ log** (`In`, `Om`). Mã phải khớp bộ đếm `next_id` trong `state.json`; lần nào không có log chứng minh thì không ghi. Lần nào không đạt thì chép log của cả 3 nguồn vào `docs/do_dac/`.

## Chuẩn bị chung

- Trên Pi: `git checkout main && git pull`, rồi bật venv `source .venv/bin/activate` (đứng ở gốc repo) và `pip install -r pi/requirements.txt "opencv-python<5"`. Mỗi cửa sổ mới (cửa sổ `tmux` mới, SSH lại sau reboot) phải bật lại venv.
- **Chạy `main.py` trong `tmux`** (cài bằng `sudo apt install tmux`): `tmux new -s safecam`, rồi chạy `main.py` như thường. Thoát ra mà chương trình vẫn chạy: Ctrl+B rồi D. Vào lại: `tmux attach -t safecam`. Lý do: K5 tắt router làm rớt SSH, nên `main.py` chạy thẳng trong cửa sổ SSH sẽ bị tắt theo.
- Mở đủ 3 nguồn log: `main.py` (Pi), `mosquitto_sub` với tài khoản `safecam_dev` (Pi), Serial ESP32 (`pio device monitor -p COM5`, laptop). Nếu muốn thì mở thêm `watch -n 1 python3 -m json.tool ~/Instrusion-Detect/data/state.json`.
- Mã sự kiện tăng dần qua các lần thử. Bảng dưới viết `In`, `Om`; khi ghi kết quả thì ghi mã thật (ví dụ I7, O3).
- **Che camera** bằng cách áp kín lòng bàn tay hoặc úp cốc tối màu lên ống kính. Che hở thì ảnh lọt sáng, không ra `lost`.
- Thông số đang dùng (tạm, chưa chọn trên val): T = 2 s, K_min = 5, p = 0,5, `lost_after_s` = 5 s, `detail_min` = 25. Đổi thông số thì ghi vào cột Ghi chú.

Log `main.py` cần biết: `Xâm nhập: alarm khu [2]`, `Xâm nhập: none khu []`, `Quan sát: lost 3`, `Quan sát: ok None`, `ACK: ['I1', 'O1'] -> acked lost_acked` (sau mũi tên là trạng thái xâm nhập, rồi trạng thái quan sát).

## K1. Đang cảnh báo → che camera → ACK → bỏ che

Mục tiêu: lúc camera bị che, Pi không được coi là "vắng người", nên không đóng sự kiện.

| Bước | Làm gì | Phải thấy gì |
| --- | --- | --- |
| 1 | Đi vào khu 2, đứng yên | Pi `Xâm nhập: alarm khu [2]`. ESP32 đỏ nháy, còi kêu |
| 2 | Vẫn đứng trong khu, che kín camera ≥ 6 s | Pi `Quan sát: lost m`. MQTTX có `event` `Om`, `state` có `pending: ["In","Om"]`. ESP32 **vẫn đỏ nháy, còi kêu** (ưu tiên 1) |
| 3 | Vẫn che, bấm nút | Serial `Bam nut: 2 ma cho gui`, `Gui ACK: {"ids":["In","Om"]}`. Pi `ACK: [...] -> acked lost_acked`. ESP32 đỏ sáng, còi tắt |
| 4 | Vẫn che, rời ra khu 0/1, chờ 10 s | **Không** có `Xâm nhập: none`. ESP32 vẫn đỏ sáng |
| 5 | Bỏ che | Khoảng 1 s sau có `Quan sát: ok None`, rồi khoảng 2 s sau nữa có `Xâm nhập: none khu []`. ESP32 xanh |

Đạt khi bước 4 không đóng sự kiện và bước 5 đóng đúng lúc. Biến thể **bỏ che lúc người vẫn trong khu** (phải giữ `acked`, đỏ sáng, cho tới khi người rời khu) chỉ kiểm bằng giả lập.

## K4. Che camera, đi vào khu, bỏ che

Mục tiêu: người lẻn vào lúc camera bị che thì vẫn bị báo ngay khi camera thấy lại, và bản tin mang nhãn "xâm nhập sau mất quan sát".

| Bước | Làm gì | Phải thấy gì |
| --- | --- | --- |
| 1 | Khu cấm vắng, ESP32 xanh. Che kín camera ≥ 6 s, **không bấm nút** | Pi `Quan sát: lost m`. ESP32 vàng nháy, bíp chậm |
| 2 | Vẫn che, đi vào khu 2, đứng yên | Không có `Xâm nhập: alarm` (camera không thấy gì) |
| 3 | Bỏ che, bấm đồng hồ | Khoảng 1 s sau Pi `Xâm nhập: alarm khu [2]`. MQTTX `event` có `"after_blind": true`. ESP32 đỏ nháy, còi kêu |
| 4 | Bấm nút, rời khu | Pi `ACK: ['In', 'Om'] -> ...`, sau đó `Quan sát: ok None`, rồi `Xâm nhập: none`. ESP32 xanh |

Đạt khi bước 3 báo động và có `after_blind: true`. Cột Số đo ghi thời gian từ lúc bỏ che tới lúc còi kêu, đo ước lượng bằng đồng hồ (độ trễ chính thức đo riêng bằng slow-motion). Lưu ý: che ngắn (chưa tới `lost`) rồi bỏ che thì sự kiện **vẫn** mang `after_blind: true`, vì lúc báo động camera còn ở `suspect`, chưa về `ok`. Đó là hành vi đúng của code hiện tại.

## K5. Đang cảnh báo → tắt router → bấm nút → bật router

Mục tiêu: mất mạng thì ESP32 vẫn giữ báo động, nút tắt được còi tại chỗ, có mạng lại thì ACK tự đồng bộ.

| Bước | Làm gì | Phải thấy gì |
| --- | --- | --- |
| 1 | Đi vào khu 2 | Pi `alarm`, ESP32 đỏ nháy, còi kêu |
| 2 | Rút điện router | Serial `Mat WiFi`, rồi khoảng 6 s sau `MAT TIN HIEU PI`. ESP32 **vẫn đỏ nháy, còi kêu** (không chuyển sang đỏ vàng xen kẽ) |
| 3 | Bấm nút | Còi tắt ngay, đèn vẫn đỏ nháy. Serial `Bam nut: 1 ma cho gui`, không có `Gui ACK` |
| 4 | Cắm điện router, bấm đồng hồ | Serial `WiFi OK`, `MQTT dang ket noi...OK`, `Gui ACK: {"ids":["In"]}`, rồi `state ... light=red buzzer=off pending=0 cho_xac_nhan=0`. ESP32 đỏ sáng, **không cần bấm lại**. Vào lại `tmux`, Pi có `ACK: ['In'] -> acked ok` |
| 5 | Rời khu | Pi `Xâm nhập: none`, ESP32 xanh |

Đạt khi bước 3 tắt được còi và bước 4 đồng bộ ACK mà không cần bấm lại. Cột Số đo ghi thời gian từ lúc cắm router tới lúc ESP32 đỏ sáng. Nếu Serial cứ báo `loi rc=...` thì Pi có thể đã đổi IP sau khi router khởi động lại: xem bằng `hostname -I` (việc đặt IP cố định chưa làm).

## K7. Đang cảnh báo → khởi động lại Pi

Mục tiêu: sự kiện chưa xác nhận không mất sau khi khởi động lại, mã sự kiện không bị đặt trùng.

**Phần A, xâm nhập**

| Bước | Làm gì | Phải thấy gì |
| --- | --- | --- |
| 1 | Đi vào khu 2 | Pi `alarm` `In`, ESP32 đỏ nháy, còi kêu |
| 2 | Dừng Pi: Ctrl+C `main.py`, hoặc `sudo reboot` | Khoảng 6 s sau Serial `MAT TIN HIEU PI`, ESP32 vẫn đỏ nháy, còi kêu |
| 3 | Chạy lại `main.py`, bấm đồng hồ | Pi `Sẵn sàng. Trạng thái xâm nhập: alarm`. MQTTX `state` có `seq` bắt đầu lại từ 1, vẫn mã `In`, `pending: ["In"]`. Serial `Nghe duoc Pi`. Lúc camera đang mở có thể thấy `Quan sát: suspect None` rồi `ok`: đó là bình thường |
| 4 | Bấm nút | Pi `ACK: ['In'] -> acked ok`, ESP32 đỏ sáng |
| 5 | Rời khu, chờ về xanh, rồi vào lại khu | Sự kiện mới mang mã `I(n+1)`, không lặp lại `In` |

**Phần B, quan sát** (việc còn chờ của Trung Anh)

| Bước | Làm gì | Phải thấy gì |
| --- | --- | --- |
| 1 | Che kín camera ≥ 6 s | Pi `Quan sát: lost m`, ESP32 vàng nháy |
| 2 | Ctrl+C, bỏ che, chạy lại `main.py` | `state` có `"obs":{"st":"lost","id":"Om"}`, `pending: ["Om"]`. ESP32 vàng nháy tiếp, dù camera đã nhìn được |
| 3 | Bấm nút | Pi `ACK: ['Om'] -> none lost_acked`, rồi `Quan sát: ok None`. ESP32 xanh |
| 4 | Che lại ≥ 6 s | Pi `Quan sát: lost m+1`, **không phải** `m` |

Thử 2 lần: lần 1 dừng bằng Ctrl+C, làm cả phần A và B; lần 2 dùng `sudo reboot` thật, làm phần A. Vì chưa có `safecam.service` nên sau khi Pi khởi động xong phải SSH vào chạy `main.py` bằng tay. Cột Số đo ghi thời gian từ lúc chạy `main.py` tới lúc Serial báo `Nghe duoc Pi`. Khi đã có service thì đo lại, tính từ lúc gõ lệnh reboot.

## K10. Người vẫn trong khu sau khi sự kiện kết thúc

Mục tiêu: sự kiện đã đóng thì không mở lại. Người quay lại khu là một sự kiện mới, còi phải kêu lại dù trước đó đã bấm nút.

| Bước | Làm gì | Phải thấy gì |
| --- | --- | --- |
| 1 | Đi vào khu 2, bấm nút | Pi `alarm` `In` → `ACK: ['In'] -> acked ok`, ESP32 đỏ sáng |
| 2 | Bước sang khu 0/1 (vẫn trong khung hình), đứng ≥ 4 s | Pi `Xâm nhập: none khu []`, ESP32 xanh |
| 3 | Bước lại vào khu 2 hoặc 3 | Pi `Xâm nhập: alarm khu [...]`. MQTTX `event` mã `I(n+1)`, `after_blind: false`. ESP32 đỏ nháy, **còi kêu lại** |

Đạt khi bước 3 có mã mới và còi kêu. Trong ghi chú, ghi thêm nếu thấy sự kiện tự đóng trong lúc người vẫn đứng trong khu, ví dụ ngồi sau bàn mà mô hình không thấy. Đó là bỏ sót của mô hình, cần ghi cho chương 3.

## K12. Rút cáp camera rồi cắm lại

Mục tiêu: mất camera thì có cảnh báo quan sát, cắm lại thì camera tự mở lại, không phải chạy lại chương trình.

| Bước | Làm gì | Phải thấy gì |
| --- | --- | --- |
| 1 | ESP32 xanh. Rút cáp USB camera khỏi Pi | Pi `Quan sát: suspect None`, rồi `Quan sát: lost m` khoảng 6–8 s sau khi rút (mất ảnh thì mỗi vòng lặp phải chờ 2 s). Pi có in `Camera lỗi, mở lại`, rồi lặp lại `Không mở được camera, thử lại sau 2s`. ESP32 vàng nháy, bíp chậm |
| 2 | Bấm nút | Pi `ACK: ['Om'] -> none lost_acked`. ESP32 vàng sáng, **chưa được về xanh** |
| 3 | Cắm lại cáp, bấm đồng hồ | Hết dòng `Không mở được camera`, rồi khoảng 1 s sau khi có ảnh thì ra `Quan sát: ok None` (tính từ lúc cắm cáp thì khoảng 10 s, vì Pi phải nhận USB, chờ lượt mở lại, C270 chỉnh phơi sáng). ESP32 xanh |
| 4 | Đi vào khu 2 | Pi `alarm`, tức camera chạy thật |
| 5 | `v4l2-ctl -d /dev/v4l/by-id/usb-046d_C270_HD_WEBCAM_288F8990-video-index0 -C power_line_frequency` | In ra `1` (50 Hz đã được đặt lại) |

Đạt khi bước 3 tự mở lại camera. Cột Số đo ghi thời gian từ lúc cắm cáp tới lúc có `Quan sát: ok`. Trường hợp cắm lại **trước** khi bấm nút (ESP32 phải giữ vàng nháy tới khi bấm, rồi về xanh) chỉ kiểm bằng giả lập.
**Không đạt** nếu rút cáp mà không thấy `Camera lỗi, mở lại`, hoặc cắm lại quá 30 s vẫn không có ảnh. Khi đó chép log lại, rồi sửa `camera.py` trên nhánh `fix/...` (mở lại khi quá lâu không có ảnh mới).

## K13. Mất điện ngay sau khi trạng thái đổi

Mục tiêu: file `state.json` không bao giờ bị ghi dở.

Rút điện có rủi ro nhỏ làm hỏng thẻ SD. Trước khi thử, chép `.env` ra laptop và kiểm tra code đã có trên GitHub.

Thử 1 lần: rút dây nguồn Pi (không dùng `sudo reboot`) trong khoảng 1 s sau khi log có `Xâm nhập: alarm`. Mọi lần đổi trạng thái (`acked`, `none`, `lost`, `lost_acked`) đều ghi file qua cùng một hàm ghi nguyên tử, nên các thời điểm khác kiểm bằng test tự động trong `pi/tests/test_persistence.py`: ghi bị ngắt thì file cũ còn nguyên (`test_old_file_survives_failed_write`), file hỏng thì không làm dừng chương trình (`test_corrupt_file_returns_none_and_kept`), khôi phục từng trạng thái (`test_acked_restored`, `test_obs_lost_restored`, `test_obs_lost_acked_restored`).

Sau khi rút, cắm điện, SSH vào và kiểm tra:

| Kiểm tra | Phải thấy gì |
| --- | --- |
| `python3 -m json.tool ~/Instrusion-Detect/data/state.json` | In ra JSON đầy đủ, có `intr` và `obs`, không báo lỗi |
| `ls ~/Instrusion-Detect/data/` | Không có `state.json.bad`. Có `state.json.tmp` sót lại thì không sao |
| Chạy `main.py` | Không lỗi. Trạng thái là trạng thái ngay trước hoặc ngay sau lần đổi cuối, không phải trạng thái nào khác. ESP32 làm theo |

Đạt khi file đọc được và trạng thái khôi phục đúng. Cột Ghi chú ghi trạng thái lúc rút và trạng thái đọc được sau khi bật lại.

## Bảng kết quả

Kết quả 23/11 (mô hình gốc): 8/8 lần đạt. Cột Số đo: K4 (bỏ che → còi), K5 (cắm router → đỏ sáng), K7 (chạy `main.py` → `Nghe duoc Pi`), K12 (cắm cáp → `ok`), đơn vị giây.

| Kịch bản | Lần | Ngày giờ | Người thử | Đạt | Số đo (s) | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| K1 | 1 | 23/11 16:55 | Trung Anh | Đạt | – | I4, O4; rời khu khi còn che, chờ 10 s không đóng sự kiện |
| K4 | 1 | 23/11 17:35 | Trung Anh | Đạt | 2 | I8, O6; after_blind true; ACK một lần cả I8 và O6 |
| K5 | 1 | 23/11 19:15 | Trung Anh | Đạt | 45 | I19; log Pi có 1 ACK I19; log Serial chỉ lưu tới `Mat WiFi` |
| K7 | 1 | 23/11 18:30 | Trung Anh | Đạt | – | Ctrl+C. A: khôi phục alarm I12, sự kiện sau I13. B: khôi phục lost O7, ACK được, che lại ra O8 |
| K7 | 2 | 23/11 18:50 | Trung Anh | Đạt | 3,5 | sudo reboot. A: khôi phục alarm I15, sự kiện sau I16 |
| K10 | 1 | 23/11 18:00 | Trung Anh | Đạt | – | I9 → none → I10, còi kêu lại |
| K12 | 1 | 23/11 16:12 | Trung Anh | Đạt | 9,48 | O2; Pi tự mở lại camera (V4L2); power_line_frequency = 1; vào khu sau khi cắm lại ra I2 |
| K13 | 1 | 23/11 17:39 (giờ Pi) | Trung Anh | Đạt | – | Rút điện ngay sau `alarm` I20: state.json đọc được, không có .bad, khôi phục alarm I20, next_id 21 |
