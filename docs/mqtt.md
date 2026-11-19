# Bản tin MQTT giữa Pi và ESP32 (chốt 19/11/2026)

Pi giữ trạng thái và tính sẵn đèn, còi; ESP32 chỉ làm theo. Riêng "mất tín hiệu từ Pi" thì ESP32 tự xử lý.

## Topic

| Topic | Chiều | QoS | Retain | Khi nào |
| --- | --- | --- | --- | --- |
| `safecam/cam01/state` | Pi → ESP32 | 1 | Có | Mỗi khi trạng thái đổi và ngay sau khi kết nối |
| `safecam/cam01/event` | Pi → ESP32 | 1 | Không | Mở sự kiện mới |
| `safecam/cam01/hb` | Pi → ESP32 | 0 | Không | Mỗi 2 giây |
| `safecam/alarm01/ack` | ESP32 → Pi | 1 | Không | Bấm nút, gửi lại mỗi giây tới khi Pi xác nhận |
| `safecam/cam01/status`, `safecam/alarm01/status` | LWT | 1 | Có | `"online"` khi kết nối; broker gửi `"offline"` khi rớt |

## Payload (JSON)

`state` (ESP32 chỉ cần đọc `light`, `buzzer`, `pending`):

```json
{"seq":120,"light":"red_blink","buzzer":"on",
 "intr":{"st":"alarm","id":"I3","zones":[2,3]},
 "obs":{"st":"ok","id":null},
 "pending":["I3"],"acked":["I2"]}
```

| Trường | Giá trị | Ý nghĩa |
| --- | --- | --- |
| `seq` | số tăng dần | Bỏ bản tin cũ đến trễ |
| `light` | `red_blink`, `red`, `yellow_blink`, `yellow`, `green` | Đèn cần bật |
| `buzzer` | `on`, `slow`, `off` | Còi: kêu liên tục, bíp nhịp chậm, tắt |
| `intr.st` | `none`, `suspected`, `alarm`, `acked` | Trùng hằng số trong `pi/safecam/intrusion.py` |
| `obs.st` | `ok`, `suspect`, `lost`, `lost_acked` | Trạng thái quan sát (`observation.py`) |
| `zones` | danh sách 0–3 | Khu đang xâm nhập, để hiển thị |
| `pending` | mã sự kiện chưa ACK | Danh sách nút sẽ ACK khi bấm |
| `acked` | vài mã vừa ACK | ESP32 thấy mã của mình ở đây thì ngừng gửi lặp lại |

`event`:

```json
{"id":"I3","type":"intrusion","zones":[2],"after_blind":false}
{"id":"O1","type":"observation","reason":"lost"}
```

`after_blind: true` là "xâm nhập sau mất quan sát" (K4).

`ack`: `{"ids":["I3","O1"]}` · `hb`: `{"seq":4521}`

Mã sự kiện là chữ: `I` xâm nhập, `O` quan sát, vì hai loại đếm số riêng.

## Đèn, còi, nút

| Ưu tiên | Tình huống | `light` | `buzzer` |
| --- | --- | --- | --- |
| 1 | Đang cảnh báo xâm nhập | `red_blink` | `on` |
| 2 | ESP32 mất tín hiệu từ Pi (ESP32 tự xử lý) | đỏ và vàng nháy xen kẽ | bíp ngắn |
| 3 | Cảnh báo quan sát chưa ACK | `yellow_blink` | `slow` |
| 4 | Xâm nhập đã ACK, chờ vắng người | `red` | `off` |
| 5 | Mất quan sát, đã ACK | `yellow` | `off` |
| 6 | Bình thường | `green` | `off` |

- Ưu tiên 1 đứng trên 2: đang cảnh báo xâm nhập mà mất kết nối thì ESP32 giữ đỏ nháy và còi.
- Mất 3 nhịp `hb` liên tiếp (6 giây) thì ESP32 chuyển sang ưu tiên 2.
- **Cả 4 nút hiện cùng một chức năng ACK.** Đang mất kết nối thì bấm nút chỉ tắt còi tại chỗ, nhớ các mã trong `pending`, có mạng lại thì gửi ACK (K5).
- Chân đèn, nút, còi: xem `hardware/sododaunoi_d.md`.

## Ví dụ theo kịch bản

| Kịch bản | Bản tin |
| --- | --- |
| Bình thường | `state` có `light: green`, `buzzer: off`, `intr.st: none`, `pending: []` |
| Đi vào khu 2 | `event` `{"id":"I1","type":"intrusion","zones":[2],"after_blind":false}`, rồi `state` có `red_blink`, `on`, `pending: ["I1"]` |
| Bấm nút | ESP32 gửi `{"ids":["I1"]}` mỗi giây → Pi gửi `state` có `intr.st: acked`, `red`, `off`, `pending: []`, `acked: ["I1"]` → ESP32 ngừng gửi |
| Vắng đủ T giây | `state` về như "Bình thường" |
| K5: tắt router lúc đang báo | ESP32 giữ đỏ nháy và còi; bấm nút thì tắt còi tại chỗ, nhớ `["I1"]`; bật router lại → nhận `state` (retain) → gửi ACK |

## Lưu ý cài đặt ESP32

- PubSubClient mặc định chỉ nhận bản tin tối đa 256 byte: gọi `client.setBufferSize(512)`, nếu không bản tin dài bị bỏ không báo lỗi.
- Đọc JSON bằng ArduinoJson.
- LWT đặt lúc `connect`: topic `safecam/alarm01/status`, nội dung `"offline"`, retain; kết nối xong tự gửi `"online"`.
