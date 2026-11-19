"""Tính đèn, còi và bản tin gửi ESP32 (docs/mqtt.md)
Pi giữ trạng thái, ESP32 chỉ làm theo: mọi quyết định đèn/còi nằm ở đây
Các hàm không giữ trạng thái nên test được mà không cần camera hay MQTT"""

from collections import deque
from .intrusion import ACKED, ALARM

# Trạng thái quan sát, trùng docs/mqtt.md. Khi observation.py có hằng số thì import từ đó
OBS_OK = "ok"
OBS_SUSPECT = "suspect"
OBS_LOST = "lost"
OBS_LOST_ACKED = "lost_acked"

def pick_light_buzzer(intr_st, obs_st):
    """Bảng ưu tiên đèn/còi: xét ưu tiên từ trên xuống, gặp dòng nào khớp thì
    trả luôn.
    Ưu tiên 2 (ESP32 mất tín hiệu từ Pi) do ESP32 tự xử lý nên không có ở đây."""
    if intr_st == ALARM: # 1. đang cảnh báo xâm nhập
        return "red_blink", "on"
    if obs_st == OBS_LOST: # 3. cảnh báo quan sát chưa ACK
        return "yellow_blink", "slow"
    if intr_st == ACKED:    # 4. Xâm nhập đã ACK, chờ vắng người
        return "red", "off"
    if obs_st == OBS_LOST_ACKED: # 5. mất quan sát, đã ACK
        return "yellow", "off"
    return "green", "off" #6. bình thường (bao gồm nghi ngờ, nghi lỗi)

def intr_code(event_id):
    """Số sự kiện xâm nhập -> mã gửi MQTT: 3 -> "I3". """
    return f"I{event_id}"

def obs_code(event_id):
    """Số sự kiện quan sát -> mã gửi MQTT: 1 -> "O1" """
    return f"O{event_id}"

def split_ack_ids(codes):
    """Mã ESP32 gửi trong ACK -> (số xâm nhập, số quan sát).
    {"I3", "O1"} -> ({3}, {1}). Mã sai dạng thì bỏ qua, không làm dừng chương trình. """
    intr_ids, obs_ids = set(), set()
    for code in codes:
        prefix, num = code[:1], code[1:]
        if not num.isdecimal(): # "", "I", "Iabc": phía sau không phải số
            continue
        if prefix == "I":
            intr_ids.add(int(num))
        elif prefix == "O":
            obs_ids.add(int(num))
    return intr_ids, obs_ids

def pending_ids(intr, obs_st, obs_id):
    """Mã sự kiện đang chờ ACK, ví dụ ["I1", "O1"].
    Nút trên ESP32 chỉ xác nhận các mã này: sự kiện mở sau lúc bấm vẫn báo tiếp.
    Trả list (không phải set) vì JSON không ghi được set."""
    ids = []
    if intr.state == ALARM:
        ids.append(intr_code(intr.event.id))
    if obs_st == OBS_LOST and obs_id is not None:
        ids.append(obs_code(obs_id))
    return ids

class RecentAcks:
    """Vài mã vừa nhận ACK, gửi trong trường "acked" của state.
    ESP32 thấy mã của mình ở đây thì ngừng gửi ACK lặp lại."""

    def __init__(self, size=5):
        # Đầy thì tự bỏ mã cũ nhất: giữ bản tin state dưới 512 byte của ESP32
        self._ids = deque(maxlen=size)

    def add(self, codes):
        """Ghi mọi mã ESP32 gửi, kể cả mã đã ACK từ trước (ví dụ sau khi Pi khởi động lại)."""
        for code in sorted(codes):
            if code not in self._ids:
                self._ids.append(code)

    def as_list(self):
        return list(self._ids) #JSON không ghi được deque, đổi sang list

def build_state(intr, obs_st, obs_id, acked):
    """Bản tin state gửi ESP32 (chưa có seq: mqtt_client.publish_state tự thêm)
    acked: danh sách mã vừa ACK, lấy từ RecentAcks.as_list()."""
    light, buzzer = pick_light_buzzer(intr.state, obs_st)
    ev = intr.event # chỉ có khi alarm hoặc acked, còn lại là None
    return {
        "light": light,
        "buzzer": buzzer,
        "intr": {
            "st": intr.state,
            "id": intr_code(ev.id) if ev else None,
            "zones": sorted(ev.zones) if ev else [], # set -> list cho JSON
        },
        "obs": {
            "st": obs_st,
            "id": obs_code(obs_id) if obs_id is not None else None,
        },
        "pending": pending_ids(intr, obs_st, obs_id),
        "acked": acked,
    }

def intrusion_event_msg(event, after_blind=False):
    """Bản tin event khi mở sự kiện xâm nhập mới.
    after_blind=True: xâm nhập sau mất quan sát (K4), do main.py quyết định"""
    return {
        "id": intr_code(event.id),
        "type": "intrusion",
        "zones": sorted(event.zones),
        "after_blind": after_blind,
    }

def observation_event_msg(obs_id, reason=OBS_LOST):
    """Bản tin event khi vào mất quan sát. """
    return {"id": obs_code(obs_id), "type": "observation", "reason": reason}
