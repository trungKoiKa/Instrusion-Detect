"""Giám sát camera: camera có đang nhìn được không 
(mất hình, bị che, Pi quá chậm).
Khung không quan sát được không bao giờ coi là "không có người" """
import cv2

DETAIL_SIZE = (64, 48) # thu nhỏ trước khi tính: xóa nhiễu hạt khi phòng tối

def image_detail(img):
    """Độ chi tiết của ảnh: độ lệch chuẩn độ sáng trên ảnh xám thu nhỏ.
    Bị che thì gần như một màu nên số nhỏ; tắt bớt đèn vẫn còn cạnh bàn, của sổ nên 
    số vẵn lớn."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, DETAIL_SIZE, interpolation=cv2.INTER_AREA)
    return float(small.std())

