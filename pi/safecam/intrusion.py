""" Trạng thái xâm nhập
KHÔNG CÓ -> NGHI NGỜ -> CẢNH BÁO -> ĐÃ XÁC NHẬN (Sau ACK) -> KẾT THÚC (khu cấm vắng đủ T giây)
Đầu vào là kết luận của zones.py cho từng khu cấm
"""

from dataclasses import dataclass, field

from .zones import ALERT, EMPTY, SUSPECT

# Các trạng thái 
NONE = "none" # không có gì
SUSPECTED = "suspected" # có thầy người nhưng chưa đủ bằng chứng
ALARM = "alarm" # đang cảnh báo, chờ người trực bấm ACK
ACKED = "acked" # đã ACK, chờ khu cấm vắng người đủ T giây

@dataclass
class Event:
    """ Một sự kiện xâm nhập: từ lúc báo động tới lúc kết thúc"""
    id: int
    start: float 
    zones: set = field(default_factory=set) # mọi khu cấm từng báo động trong sự kiện
    end: float | None = None

class Intrusion:
    def __init__(self, next_id=1):
        self.state = NONE
        self.event = None # sự kiện đang mở (ALARM HOẶC ACKED)
        self.last_closed = None # sự kiện vừa kết thúc, để main.py ghi log
        self.next_id = next_id # persistence.py sẽ khôi phục số này khi khởi động lại

    def update(self, now, verdicts):
        """Gọi mỗi vòng với {khu cấm: kết luận}. Trả về True nếu có gì thay đổi."""
        alert_zones = {z for z, v in verdicts.items() if v == ALERT}
        any_suspect = any(v == SUSPECT for v in verdicts.values())
        all_empty = all(v == EMPTY for v in verdicts.values())
        old_state = self.state
        old_zones = set(self.event.zones) if self.event else set()

        if self.state in (NONE, SUSPECTED):
            if alert_zones:
                self._open(now, alert_zones)
            elif any_suspect:
                self.state = SUSPECTED
            elif all_empty:
                self.state = NONE
            # Còn lại là UNKNOWN: giữ nguyên, không kết luận gì
        elif self.state == ALARM:
            #Không tự tắt khi người rời đi: chỉ ACK mới đưa sang ACKED
            self.event.zones |= alert_zones
        elif self.state == ACKED:
            self.event.zones |= alert_zones
            # Chỉ EMPTY mới là vắng; UNKNOWN (Che cam, Pi chậm) không kết thúc sự kiện
            if all_empty:
                self._close(now)

        new_zones = self.event.zones if self.event else set()
        return self.state != old_state or new_zones != old_zones

    def ack(self, event_ids):
        """ Người trực bấm nút: xác nhận các sự kiện có id trong event_ids
        Sự kiện mở sau lúc bấm không có trong danh sách nên vẫn báo tiếp"""
        if self.state == ALARM and self.event.id in event_ids:
            self.state = ACKED
            return True
        return False

    def _open(self, now, zones):
        self.event = Event(self.next_id, now, set(zones))
        self.next_id += 1
        self.state = ALARM

    def _close(self, now):
        self.event.end = now
        self.last_closed = self.event
        self.event = None
        self.state = NONE

