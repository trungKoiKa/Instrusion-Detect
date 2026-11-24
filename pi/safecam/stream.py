"""Luồng hình MJPEG có vẽ khu và khung người,xem trên laptop khi demo (đề xuất mục 8)."""
import cv2

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