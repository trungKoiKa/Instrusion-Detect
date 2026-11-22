"""
Lưu trạng thái ra file mỗi lần thay đổi, khôi phục khi 
khởi động lại (K7, K13)

Ghi kiểu "nguyên tử": ghi ra file tạm, ép xuống thẻ nhớ (fsync), rồi đổi tên đè 
file cũ, mất điện giữa chừng thì file cũ vẫn còn nguyên, không bao giờ bị nửa vời
"""
import json 
import os
from pathlib import Path 

from .intrusion import ACKED, ALARM, NONE, Event, Intrusion
from .observation import OBS_LOST, OBS_LOST_ACKED, Observation

def save_state(path, data):
    """Chỉ ghi data ra file JSON, an toàn khi mất điện"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno()) # ép dữ liệu xuống thẻ nhớ trước khi đổi tên
    os.replace(tmp, path) # đổi tên là một bước duy nhất: hoặc file cũ, hoặc file mới
    if hasattr(os, "O_DIRECTORY"): # Linux (Pi): ghi luôn việc đổi tên xuống thẻ nhớ
        fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

def load_state(path):
    """Đọc file trạng thái. Chưa có file hoặc file hỏng thì trả None"""
    path = Path(path)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Giữ lại file hỏng để xem sau, không xóa evidence
        path.replace(path.with_name(path.name + ".bad"))
        return None

def intrusion_to_dict(it):
    """Chỉ lưu những gì cần để báo tiếp sau khi khởi động lại.""" 
    ev = it.event
    return{
        "state": it.state,
        "next_id": it.next_id,
        "event": None if ev is None else {
            "id": ev.id,
            "start": ev.start,
            "zones": sorted(ev.zones) # set không ghi được ra JSON, đổi thành list
        },
    }

def intrusion_from_dict(d):
    """Tạo lại Intrusion từ dict, Sự kiện chưa kết thúc (ALARM, ACKED) được khôi phục"""
    it = Intrusion(next_id=d.get("next_id", 1))
    ev = d.get("event")
    if d.get("state") in (ALARM, ACKED) and ev:
        it.event = Event(ev["id"], ev["start"], set(ev["zones"]))
        it.state = d["state"]
    else:
        it.state = NONE #Nghi ngờ chỉ là tạm thời, khởi động lại thì xét lại từ đầu
    return it

def observation_to_dict(obs):
    """Chỉ lưu những gì cần để báo tiếp. Không lưu bad_since, last_bad:
    đó là giờ monotonic, khởi động lại thì về 0, vô nghĩa."""
    return {
        "state": obs.state,
        "event_id": obs.event_id,
        "next_id": obs.next_id,
    }

def observation_from_dict(d, lost_after_s):
    """Tạo lại Observation. Cảnh báo quan sát chưa kết thúc (LOST, LOST_ACKED) được khôi phục"""
    obs = Observation(lost_after_s, next_id=d.get("next_id", 1))
    if d.get("state") in (OBS_LOST, OBS_LOST_ACKED) and d.get("event_id") is not None:
        obs.state = d["state"]
        obs.event_id = d["event_id"]
    # còn lại giữ OBS_OK như lúc mới tạo: nghi lỗi chỉ là tạm thời
    return obs