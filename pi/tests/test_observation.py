import numpy as np 
from safecam.observation import image_detail

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