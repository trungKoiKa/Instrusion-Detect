"""Giám sát camera: camera có đang nhìn được không 
(mất hình, bị che, Pi quá chậm).
Khung không quan sát được không bao giờ coi là "không có người" """
import cv2

OBS_OK = "ok" # nhìn tốt
OBS_SUSPECT = "suspect" # vừa thấy lỗi, chờ xem có kéo dài không
OBS_LOST = "lost" # lỗi đủ lâu: cảnh báo quan sát, chờ ACK
OBS_LOST_ACKED = "lost_acked" # đã ACK, chờ camera nhìn lại được 

DETAIL_SIZE = (64, 48) # thu nhỏ trước khi tính: xóa nhiễu hạt khi phòng tối

def image_detail(img):
    """Độ chi tiết của ảnh: độ lệch chuẩn độ sáng trên ảnh xám thu nhỏ.
    Bị che thì gần như một màu nên số nhỏ; tắt bớt đèn vẫn còn cạnh bàn, cửa sổ nên 
    số vẫn lớn."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, DETAIL_SIZE, interpolation=cv2.INTER_AREA)
    return float(small.std())

class Observation:
    """OK -> SUSPECT -> LOST (lỗi đủ lost_after_s giây) -> LOST_ACKED (sau ACK) -> OK.
    Mỗi vòng main.py chỉ báo một câu: lượt này có nhìn được không (good)."""

    def __init__(self, lost_after_s, next_id=1):
        if lost_after_s <= 0:
            raise ValueError("lost_after_s phải >0")
        self.lost_after_s = lost_after_s
        self.state = OBS_OK
        self.event_id = None # Số sự kiện khi LOST/LOST_ACKED, còn lại None
        self.next_id = next_id
        self.bad_since = None # Lúc bắt đầu lỗi; None khi đang nhìn tốt
        self.last_bad = None   # lần cuối không nhìn được; None khi chưa lỗi lần nào

    @classmethod
    def from_config(cls, cfg):
        return cls(cfg["lost_after_s"])

    def update(self, now, good):
        # Gọi mỗi vòng, Trả về True nếu trạng thái đổi
        old = self.state
        if good:
            self.bad_since = None
        else:
            self.last_bad = now
            if self.bad_since is None:
                self.bad_since = now

        if self.state == OBS_OK:
            if not good:
                self.state = OBS_SUSPECT
        elif self.state == OBS_SUSPECT:
            if good:
                self.state = OBS_OK # lỗi ngắn (ảnh đen lúc mở camera, che thoáng qua)
            elif now - self.bad_since >= self.lost_after_s:
                self.state = OBS_LOST
                self.event_id = self.next_id
                self.next_id += 1
        elif self.state == OBS_LOST_ACKED:
            if good:
                self.state = OBS_OK
                self.event_id = None
        # OBS_LOST: Không tự tắt khi camera nhìn lại được, chỉ ACK mới đưa sang LOST_ACKED
        return self.state != old

    def ack(self, event_ids):
        """Người trực bấm nút: chỉ xác nhận sự kiện đang mở có mã trong event_ids."""
        if self.state == OBS_LOST and self.event_id in event_ids:
            self.state = OBS_LOST_ACKED
            return True
        return False

    def clear_for(self, now, seconds):
        """Camera đã nhìn tốt liên tục ít nhất `seconds` giây chưa.
        Chưa đủ thì cửa sổ khu có thể lẫn ảnh che dở: không được tin kết luận "vắng" (K1)."""
        return self.last_bad is None or now - self.last_bad >= seconds