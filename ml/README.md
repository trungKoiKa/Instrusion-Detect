# ml – dữ liệu và huấn luyện (chạy trên Colab)

- `notebooks/`: train thử coco8, fine-tune, đánh giá gốc và fine-tune.
- `dataset.yaml`: 80 tên lớp COCO, chỉ dùng nhãn person (id 0).
- Script: trích khung, lọc ảnh trùng, chuyển nhãn, chia tập theo buổi quay.
- Tập test: `test_normal`, `test_hard` (nhãn điều kiện), `test_external` (COCO val2017 đã lọc). Dữ liệu thật nằm trong `data/` hoặc Google Drive.
