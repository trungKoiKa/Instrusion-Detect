"""Test hàm vẽ của stream: chạy trên laptop, không cần camera hay YOLO."""
from types import SimpleNamespace

import numpy as np

from safecam.stream import GREEN, draw_overlay, zone_edges

BOUNDARIES = [160, 320, 480]
FORBIDDEN = [2, 3]


def make_img():
    """Ảnh xám đều 480x640, mọi điểm [128, 128, 128]."""
    return np.full((480, 640, 3), 128, np.uint8)


def person(x1, y1, x2, y2, conf=0.9):
    """Người giả: draw_overlay chỉ đọc 5 thuộc tính này."""
    return SimpleNamespace(x1=x1, y1=y1, x2=x2, y2=y2, conf=conf)


def test_zone_edges():
    assert zone_edges(BOUNDARIES, 640) == [(0, 160), (160, 320), (320, 480), (480, 640)]


def test_does_not_modify_input():
    img = make_img()
    before = img.copy()
    draw_overlay(img, [person(500, 100, 600, 400)], BOUNDARIES, FORBIDDEN, "X")
    assert np.array_equal(img, before)  # ảnh của main.py không bị vẽ lên


def test_forbidden_zone_tinted():
    out = draw_overlay(make_img(), [], BOUNDARIES, FORBIDDEN, "X")
    b, g, r = out[240, 400]  # giữa khu 2 (khu cấm), không trúng vạch hay chữ
    assert r > b and r > g
    assert np.array_equal(out[240, 100], [128, 128, 128])  # khu 0 giữ nguyên


def test_person_box_green():
    out = draw_overlay(make_img(), [person(500, 100, 600, 400)], BOUNDARIES, FORBIDDEN, "X")
    assert tuple(int(v) for v in out[250, 500]) == GREEN  # cạnh trái khung, vẽ sau khi trộn đỏ


def test_no_detections():
    img = make_img()
    out = draw_overlay(img, [], BOUNDARIES, FORBIDDEN, "X")
    assert out.shape == img.shape