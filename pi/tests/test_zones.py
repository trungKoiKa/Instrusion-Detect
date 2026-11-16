from collections import namedtuple

import pytest

from safecam.zones import (ALERT, EMPTY, SUSPECT, UNKNOWN, ZoneMonitor,
                           occupied_zones, zone_of)

P = namedtuple("P", "cx")  # người giả: chỉ cần tâm ngang
BOUNDS = [160, 320, 480]
FPS = 7.5  # đo trên Pi: 7,47 FPS


def make_monitor():
    return ZoneMonitor(BOUNDS, forbidden=[2, 3], window_s=2.0, k_min=5, p=0.5, n_min=8)


def feed(mon, t0, seconds, people, fps=FPS):
    """Đưa ảnh giả vào trong `seconds` giây, trả về thời điểm cuối."""
    t = t0
    for _ in range(int(seconds * fps)):
        t += 1 / fps
        mon.add_frame(t, people)
    return t


@pytest.mark.parametrize("cx, zone", [(0, 0), (159.9, 0), (160, 1), (400, 2), (639, 3)])
def test_zone_of(cx, zone):
    assert zone_of(cx, BOUNDS) == zone


def test_occupied_zones_two_people_same_zone():
    assert occupied_zones([P(400), P(450), P(10)], BOUNDS) == {0, 2}


def test_person_in_allowed_zone_no_alert():
    mon = make_monitor()
    t = feed(mon, 0, 3, [P(50)])
    assert mon.verdicts(t) == {2: EMPTY, 3: EMPTY}


def test_person_in_forbidden_zone_alerts_within_2s():
    mon = make_monitor()
    t = feed(mon, 0, 3, [])
    t_enter = t
    while mon.verdicts(t)[2] != ALERT:
        t = feed(mon, t, 1 / FPS, [P(400)])
    assert t - t_enter < 2.0
    assert mon.verdicts(t)[3] == EMPTY


def test_single_false_positive_is_only_suspect():
    mon = make_monitor()
    t = feed(mon, 0, 1, [])
    t = feed(mon, t, 1 / FPS, [P(600)])
    t = feed(mon, t, 1, [])
    assert mon.verdicts(t)[3] == SUSPECT


def test_camera_lost_is_unknown_not_empty():
    mon = make_monitor()
    t = feed(mon, 0, 3, [P(400)])
    assert mon.verdicts(t)[2] == ALERT
    # Camera mất 3 giây: không có ảnh nào được thêm vào
    assert mon.verdicts(t + 3)[2] == UNKNOWN


def test_slow_pi_is_unknown():
    mon = make_monitor()
    t = feed(mon, 0, 3, [], fps=2)
    assert mon.verdicts(t)[2] == UNKNOWN


def test_empty_after_person_leaves_for_T():
    mon = make_monitor()
    t = feed(mon, 0, 3, [P(400)])
    t = feed(mon, t, 1, [])
    assert mon.verdicts(t)[2] != EMPTY
    t = feed(mon, t, 1.2, [])
    assert mon.verdicts(t)[2] == EMPTY


def test_boundaries_must_be_sorted():
    with pytest.raises(ValueError):
        ZoneMonitor([320, 160, 480], [2], 2.0, 5, 0.5, 8)

def test_from_config():
    mon = ZoneMonitor.from_config({"boundaries":BOUNDS, "forbidden": [2, 3]},
                                    {"window_s": 2.0, "k_min": 5, "p": 0.5, "n_min": 8})
    assert set(mon.windows) == {2, 3}

def test_boundaries_must_not_repeat():
    with pytest.raises(ValueError):
        ZoneMonitor([160, 160, 480], [2], 2.0, 5, 0.5, 8)

def test_forbidden_zone_must_exist():
    with pytest.raises(ValueError):
        ZoneMonitor(BOUNDS, [7], 2.0, 5, 0.5, 8)

def test_forbidden_must_not_be_empty():
    with pytest.raises(ValueError):
        ZoneMonitor(BOUNDS, [], 2.0, 5, 0.5, 8)

@pytest.mark.parametrize("window_s, k_min, p, n_min", [
    (0, 5, 0.5, 8),   # cửa sổ 0 giây
    (2.0, 0, 0.5, 8), # k_min = 0
    (2.0, 5, 0, 8),   # p = 0
    (2.0, 5, 1.5, 8), # p > 1
    (2.0, 5, 0.5, 0), # n_min = 0
])

def test_bad_window_params(window_s, k_min, p, n_min):
    with pytest.raises(ValueError):
        ZoneMonitor(BOUNDS, [2], window_s, k_min, p, n_min)