# ml – dữ liệu và huấn luyện (chạy trên Colab)

- `notebooks/`: một notebook: gộp nhãn CVAT, kiểm tra dữ liệu, fine-tune `yolo11n.pt` ở 320 px (augmentation mặc định), đánh giá gốc và fine-tune trên test, xuất NCNN.
- Dữ liệu: `dataset/images|labels/{train,val,test}`, một lớp `person`, chia theo video, không theo ảnh. Dữ liệu thật nằm trong `data/` hoặc Google Drive, không lên git.
