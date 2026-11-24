"""Luồng hình MJPEG có vẽ khu và khung người,xem trên laptop khi demo (đề xuất mục 8)."""
import cv2
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
# Màu theo thứ tự BGR của OpenCV
RED = (0, 0, 255)
YELLOW = (0, 255, 255)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ZONE_ALPHA = 0.25 # Độ đậm lớp đỏ phủ khu cấm: 0 là không thấy, 1 là đỏ đặc
FONT = cv2.FONT_HERSHEY_SIMPLEX

def zone_edges(boundaries, width):
    """[(x trái, x phải)] của từng khu, khu z ở vị trí z."""
    xs = [0] + list(boundaries) + [width]
    return list(zip(xs, xs[1:]))

def draw_overlay(img, detections, boundaries, forbidden, status):
    """Trả về bản sao của img đã vẽ khu, khung người và dòng trạng thái.
    Không sửa img. status phải không dấu vì cv2.putText chỉ vẽ được ASCII"""
    out = img.copy()
    h, w = out.shape[:2]

    # Khu cấm: tô đỏ đặc lên một bản sao rồi trộn với ảnh thật, ra đỏ nhạt
    tint = out.copy()
    for z, (x1, x2) in enumerate(zone_edges(boundaries, w)):
        if z in forbidden:
            cv2.rectangle(tint, (x1, 0), (x2, h), RED, -1)
    out = cv2.addWeighted(tint, ZONE_ALPHA, out, 1 - ZONE_ALPHA, 0)

    # Vạch ranh giới và số khu ở mép trên
    for x in boundaries:
        cv2.line(out, (int(x), 0), (int(x), h), YELLOW, 2)
    for z, (x1, _) in enumerate(zone_edges(boundaries, w)):
        cv2.putText(out, str(z), (int(x1) + 5, 20), FONT, 0.6, YELLOW, 2)

    # Khung người kèm độ tin cậy
    for d in detections:
        p1 = (int(d.x1), int(d.y1))
        p2 = (int(d.x2), int(d.y2))
        cv2.rectangle(out, p1, p2, GREEN, 2)
        cv2.putText(out, f"{d.conf:.2f}", (p1[0], max(p1[1] - 5, 15)), FONT, 0.5, GREEN, 1)
    # dòng trạng thái trên nền đen ở đáy ảnh cho dễ đọc
    cv2.rectangle(out, (0, h-24), (w, h), BLACK, -1)
    cv2.putText(out, status, (5, h-7), FONT, 0.5, WHITE, 1)
    return out

class StreamServer:
    """Phát luồng MJPEG. main.py chỉ gọi publish(); vẽ và mã hóa JPEG chạy ở luồng
    của từng trình duyệt đang xem, không ai xem thì không tốn CPU."""

    def __init__(self, port, boundaries, forbidden, jpeg_quality=70):
        self.port = port
        self.boundaries = boundaries
        self.forbidden = forbidden
        self.quality = jpeg_quality
        self.cond = threading.Condition()
        self.latest = None  # (seq, ảnh, detections, status): chỉ giữ ảnh mới nhất
        self.seq = 0
        self.server = None

    def publish(self, img, detections, status):
        """Gọi từ vòng lặp chính: chỉ cất lại rồi báo, không vẽ, không mã hóa."""
        with self.cond:
            self.seq += 1
            self.latest = (self.seq, img, detections, status)
            self.cond.notify_all()

    def wait_frame(self, after_seq, timeout=2.0):
        """Chờ ảnh mới hơn after_seq; hết giờ thì trả None."""
        with self.cond:
            self.cond.wait_for(lambda: self.latest is not None and self.latest[0] > after_seq, timeout)
            if self.latest is not None and self.latest[0] > after_seq:
                return self.latest
            return None

    def render_jpeg(self, img, detections, status):
        out = draw_overlay(img, detections, self.boundaries, self.forbidden, status)
        ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
        return buf.tobytes() if ok else None

    def start(self):
        """Mở cổng ở luồng riêng. Cổng bận thì báo rồi trả False, main.py chạy tiếp."""
        try:
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), _Handler)
        except OSError as e:
            print(f"Stream: không mở được cổng {self.port} ({e}), chạy tiếp không có stream")
            self.server = None
            return False
        self.server.stream = self          # để _Handler tìm được hộp thư
        self.server.daemon_threads = True  # main.py tắt thì các luồng xem tắt theo
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        print(f"Stream: mở http://<ip-pi>:{self.port} trên laptop cùng WiFi")
        return True

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()


class _Handler(BaseHTTPRequestHandler):
    """Mỗi trình duyệt đang xem có một _Handler chạy ở luồng riêng."""

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        stream = self.server.stream
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        seq = 0
        try:
            while True:
                item = stream.wait_frame(seq)
                if item is None:  # 2 giây không có ảnh mới: chờ tiếp
                    continue
                seq, img, detections, status = item
                jpg = stream.render_jpeg(img, detections, status)
                if jpg is None:
                    continue
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(jpg)}\r\n\r\n".encode())
                self.wfile.write(jpg)
                self.wfile.write(b"\r\n")
        except ConnectionError:
            pass  # laptop đóng tab: chỉ kết thúc lượt xem này

    def log_message(self, format, *args):
        pass  # không in mỗi lần có kết nối, giữ log main.py gọn