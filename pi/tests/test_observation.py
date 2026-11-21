import numpy as np 
from safecam.observation import (OBS_LOST, OBS_LOST_ACKED, OBS_OK, OBS_SUSPECT,
                                 Observation, image_detail)
def test_flat_image_has_no_detail():
    # Ảnh một màu: giống tay che kín ống kính
    img = np.full((480, 640, 3), 120, np.uint8)
    assert image_detail(img) < 1

def test_half_black_half_white_has_detail():
    img = np.zeros((480, 630, 3), np.uint8)
    img[:, 320:] = 255
    assert image_detail(img) > 50

def test_noise_is_removed_by_shrinking():
    """ Ảnh một màu + nhiễu hạt mạnh: giống bị che lúc camera tăng độ nhạy"""
    rng = np.random.default_rng(0)
    noise = rng.integers(-40, 41, (480, 640, 3))
    img = np.clip(120 + noise, 0, 255).astype(np.uint8)
    assert img.std() > 20          # ảnh gốc: nhiễu làm std lớn giả
    assert image_detail(img) < 5   # thu nhỏ xong: nhiễu mất

def make_lost():
    obs = Observation(lost_after_s=5)
    obs.update(0, False)
    obs.update(5, False)
    return obs


def test_starts_ok():
    obs = Observation(5)
    assert obs.state == OBS_OK
    assert obs.event_id is None


def test_short_fault_goes_back_ok():
    # Ảnh đen ~3,5 giây lúc mở camera: không được cảnh báo
    obs = Observation(5)
    assert obs.update(0, False) is True
    assert obs.state == OBS_SUSPECT
    obs.update(3.5, False)
    assert obs.state == OBS_SUSPECT
    assert obs.update(4, True) is True
    assert obs.state == OBS_OK
    assert obs.event_id is None


def test_long_fault_opens_event():
    obs = make_lost()
    assert obs.state == OBS_LOST
    assert obs.event_id == 1


def test_good_frame_resets_timer():
    # Lỗi 4 giây, nhìn lại được, lỗi tiếp 4 giây: không cộng dồn thành 8
    obs = Observation(5)
    obs.update(0, False)
    obs.update(4, False)
    obs.update(4.5, True)
    obs.update(5, False)
    obs.update(9, False)
    assert obs.state == OBS_SUSPECT


def test_lost_stays_after_camera_recovers():
    obs = make_lost()
    assert obs.update(6, True) is False
    assert obs.state == OBS_LOST


def test_ack_wrong_id_ignored():
    obs = make_lost()
    assert obs.ack({99}) is False
    assert obs.state == OBS_LOST


def test_ack_then_good_back_to_ok():
    obs = make_lost()
    assert obs.ack({1}) is True
    assert obs.state == OBS_LOST_ACKED
    obs.update(6, False)              # vẫn bị che: giữ LOST_ACKED
    assert obs.state == OBS_LOST_ACKED
    assert obs.update(7, True) is True
    assert obs.state == OBS_OK
    assert obs.event_id is None


def test_new_fault_after_recovery_opens_new_event():
    obs = make_lost()
    obs.ack({1})
    obs.update(6, True)
    obs.update(10, False)
    obs.update(15, False)
    assert obs.state == OBS_LOST
    assert obs.event_id == 2

def test_clear_for_needs_continuous_good():
    obs = Observation(5)
    obs.update(0, True)
    assert obs.clear_for(0, 2) is True    # chưa lỗi lần nào
    obs.update(1, False)                  # một ảnh lỗi lúc 1 giây
    obs.update(1.5, True)
    assert obs.clear_for(2.9, 2) is False  # mới tốt liên tục 1,9 giây
    assert obs.clear_for(3.1, 2) is True


def test_flicker_keeps_clear_false():
    # Tay đang đưa vào: suspect/ok xen kẽ thì không lúc nào được tin "vắng"
    obs = Observation(5)
    for t in (0, 0.4, 0.8, 1.2, 1.6):
        obs.update(t, False)
        obs.update(t + 0.2, True)
    assert obs.clear_for(2.0, 2) is False