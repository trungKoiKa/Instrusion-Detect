""" Chia khung hình thành các khu dọc (đã cấu hình sẵn)
, xét cửa số T giây cho từng khu cấm.
"""
from bisect import bisect_right
from collections import deque

# Kết luận của 1 cửa sổ
ALERT = "alert" # đủ bằng chứng có người: K_min lần và tỷ lệ >= p
SUSPECT = "suspect" # có thấy người nhưng chưa đủ bằng chứng
EMPTY = "empty" # quan sát đủ ảnh, không thấy ia suốt T giây
UNKNOWN = "unknown" # quá ít ảnh trong cửa sổ, không được kết luận "vắng"

def zone_of(cx, boundaries):
    """Số thứ tự khu chứa tọa độ ngang cx.
    boundaries là các mốc x tăng dần."""
    return bisect_right(boundaries, cx)

def occupied_zones(detections, boundaries):
    """Tập các khu có ít nhất một người trong ảnh,
    detections chỉ cần có thuộc tính cx."""
    return {zone_of(d.cx, boundaries) for d in detections}

class ZoneWindow:
    """ Cửa sổ trượt T giây của 1 khu: nhớ mỗi ảnh
    đã xử lý có thấy người hay không. """
    def __init__(self, window_s, k_min, p, n_min):
        self.window_s = window_s
        self.k_min = k_min
        self.p = p
        self.n_min = n_min
        self.samples = deque() # (thời điểm, có người)

    def add(self, now, seen):
        self.samples.append((now, seen))
        self._trim(now)

    def _trim(self, now):
        # Bỏ các mẫu cũ hơn T giây
        while self.samples and self.samples[0][0] <= now - self.window_s:
            self.samples.popleft()
    
    def counts(self, now):
        """ (Số ảnh trong cửa sổ, số ảnh thấy người)."""
        self._trim(now)
        n = len(self.samples)
        hits = sum(1 for _, seen in self.samples if seen)
        return n, hits
    
    def verdict(self, now):
        n, hits = self.counts(now)
        # Xét báo động trước: dù Pi chậm, đã đủ bằng chứng thì vẫn báo
        if hits >= self.k_min and hits / n >= self.p:
            return ALERT
        if n < self.n_min:
            return UNKNOWN
        if hits > 0:
            return SUSPECT
        return EMPTY

class ZoneMonitor:
    """Giữ một ZoneWindow cho mỗi khu cấm."""

    def __init__(self, boundaries, forbidden, window_s, k_min, p, n_min):
        if list(boundaries) != sorted(boundaries):
            raise ValueError("boundaries phải tăng dần.")
        self.boundaries = list(boundaries)
        self.windows = {z : ZoneWindow(window_s, k_min, p, n_min) for z in forbidden}

    @classmethod
    def from_config(cls, zone_cfg, det_cfg):
        return cls(zone_cfg["boundaries"], zone_cfg["forbidden"],
                    det_cfg["window_s"], det_cfg["k_min"], 
                    det_cfg["p"], det_cfg["n_min"])

    def add_frame(self, now, detections):
        """Gọi cho MỖI ảnh YOLO đã xử lý xong. Ảnh mất/không đọc được thì không gọi."""
        occupied = occupied_zones(detections, self.boundaries)
        for zone, window in self.windows.items():
            window.add(now, zone in occupied)
        return occupied
        
    def verdicts(self, now):
        """{khu cấm: kết luận}."""
        return {zone: w.verdict(now) for zone, w in self.windows.items()}


