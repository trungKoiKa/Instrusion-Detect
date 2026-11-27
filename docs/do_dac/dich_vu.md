# Dịch vụ safecam: tự chạy, tự chạy lại, watchdog

Thử 27/11/2026 trên Pi, nhánh `feat/safecam-service`, mô hình gốc. Unit: `deploy/safecam.service` (`Type=notify`, `Restart=always`, `RestartSec=5`, `WatchdogSec=15`, `TimeoutStartSec=180`, `TimeoutStopSec=15`). Mục đích: bỏ hạn chế "phải chạy tay, chưa có watchdog" và đo thời gian tự khôi phục.

## Cách làm

- Hai cửa sổ SSH: một cửa sổ xem log `sudo journalctl -u safecam -f -o short-precise` (giờ có mili giây), một cửa sổ ra tay.
- Ghi giờ ra tay ngay trên dòng lệnh: `date +%T.%N; sudo kill -9 $(systemctl show -p MainPID --value safecam)`.
- Thời gian khôi phục = giờ dòng `Sẵn sàng` trong log trừ giờ ra tay. `Sẵn sàng` in ngay trước `READY=1`, systemd in `Started` cùng mili giây đó.

## Kết quả

| Phép thử | Ra tay | systemd phát hiện | `Sẵn sàng` | Khôi phục |
| --- | --- | --- | --- | --- |
| Chết: `kill -9` | 18:19:37.077 | 18:19:37.216 `status=9/KILL` | 18:19:51.278 | **14,2 s** |
| Treo: `kill -STOP` | 18:20:49.704 | 18:21:04.415 `Watchdog timeout (limit 15s)`, SIGABRT, `Failed with result 'watchdog'` | 18:21:18.646 | **28,9 s** |
| Chết lúc đang báo động (I69, chưa ACK) | 18:23:49.360 | 18:23:49.495 | 18:24:03.555, `Trạng thái xâm nhập: alarm` | **14,2 s**; ESP32 vẫn đỏ nháy, ACK lúc 18:24:15 đúng mã `I69`, `state.json` có `next_id` 70 |
| `sudo systemctl stop safecam` | 18:25:22.928 | in `Đang tắt...` lúc 18:25:23.101 | – | Tắt xong sau **2,6 s**, `status=0/SUCCESS`, `inactive (dead)`, không tự chạy lại |
| Khởi động lại Pi (23:30, không đụng vào Pi) | bấm Reboot | WiFi vào lúc 23:30:44.5; dịch vụ `Starting` 23:30:47.3 | 23:31:51.950 | Khởi động **64,6 s**; ESP32 về xanh khoảng 2 phút sau khi bấm |

- Chạy lại khi Pi đang chạy (thư viện đã nằm trong RAM): từ `Starting` tới `Sẵn sàng` khoảng **9 s** (8,9; 9,0; 8,9 s).
- Khởi động ngay sau khi Pi bật: **64,6 s** và **89,7 s** (18:35:52.804 → 18:37:22.483), phần lớn là nạp thư viện Python từ thẻ nhớ. 89,7 s sát mặc định 90 s của systemd nên đặt `TimeoutStartSec=180`.
- Treo thật: 20:59:35 watchdog dừng tiến trình 1501 (sau `Quan sát: lost 21` lúc 20:59:14) và chạy lại lúc 20:59:56. Chưa rõ vòng lặp đứng vì sao.

## Phát hiện khi thử

- **Pi có lần không tự vào WiFi sau khi khởi động lại**: NetworkManager báo `association took too long` vài lần rồi `failed (reason 'no-secrets')` và bỏ cuộc (Pi vẫn thấy `Tenda_5CD458`, sóng 100). Đã đặt thử lại mãi và tắt tiết kiệm điện WiFi: `sudo nmcli connection modify Tenda_5CD458 connection.autoconnect-retries 0 802-11-wireless.powersave 2`. Lần khởi động lại sau đó tự vào WiFi.
- Pi không lưu log qua lần khởi động (`no persistent journal`) nên lần lỗi WiFi đầu không xem lại được.
- Pi không có RTC: khởi động khi chưa đồng bộ NTP thì giờ trong log nhảy (ví dụ `Starting` 19:31:22, `Started` 20:59:03), không dùng giờ đó để đo.

## Giới hạn

- Mỗi phép thử một lần. Khởi động lại sau khi sửa WiFi mới thử một lần; chưa thử rút điện cắm lại.
- Giờ ESP32 về xanh ước lượng bằng mắt.
