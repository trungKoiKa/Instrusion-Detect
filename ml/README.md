# ml – dữ liệu và huấn luyện (chạy trên Colab)

- `notebooks/`: một notebook: gộp nhãn CVAT, kiểm tra dữ liệu, fine-tune `yolo11n.pt` ở 320 px (augmentation mặc định), đánh giá gốc và fine-tune trên test, xuất NCNN.
- Dữ liệu: `dataset/images|labels/{train,val,test}`, một lớp `person`, chia theo phiên chụp, không theo ảnh. Dữ liệu thật nằm trong `data/` hoặc Google Drive, không lên git.
- Chia tập (đã khóa 17/11, mỗi phiên 219 ảnh sau khi bỏ ảnh `_0001` bị đen):

  | Tập | Phiên | Ghi chú |
  | --- | --- | --- |
  | train | s01, s02, s04, s06 | s01–s02 góc bàn, s04 góc cửa sổ, s06 góc cửa sổ ánh sáng yếu |
  | val | s03 | chọn `conf`, T, K_min, p ở đây |
  | test | s05, s07 | góc cửa sổ; s07 chụp ngày khác (18/11). Chỉ chạy `model.val(split="test")` một lần cuối |
