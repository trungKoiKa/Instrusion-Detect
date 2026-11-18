"""Gộp ảnh (data/raw) và nhãn CVAT (data/labels_cvat/*.zip) thành dataset cho YOLO.

Kết quả:
    data/dataset/images/{train,val,test}/*.jpg
    data/dataset/labels/{train,val,test}/*.txt
    data/dataset/data.yaml
    data/dataset.zip            (tải file này lên Google Drive)

Chia theo phiên (đã khóa 17/11), không chia theo ảnh.
Chạy từ thư mục gốc dự án:
    python tools/build_dataset.py
"""

import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # thư mục gốc dự án
RAW = ROOT / "data" / "raw"
LABELS = ROOT / "data" / "labels_cvat"
OUT = ROOT / "data" / "dataset"

# Chia tập theo phiên, khớp bảng trong ml/README.md
SPLITS = {
    "train": ["s01", "s02", "s04", "s06"],
    "val": ["s03"],
    "test": ["s05", "s07"],
}


def read_cvat_labels():
    """Đọc mọi file zip CVAT, trả về dict: tên ảnh (không đuôi) -> nội dung nhãn."""
    labels = {}
    for zp in sorted(LABELS.glob("*.zip")):
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                if name.startswith("obj_train_data/") and name.endswith(".txt"):
                    stem = Path(name).stem      # "obj_train_data/s01_0023.txt" -> "s01_0023"
                    labels[stem] = z.read(name).decode()
    return labels


def main():
    labels = read_cvat_labels()
    print(f"Đọc được {len(labels)} file nhãn từ {LABELS}")

    # Xóa dataset cũ để không sót ảnh đã bỏ từ lần chạy trước
    if OUT.exists():
        shutil.rmtree(OUT)

    for split, sessions in SPLITS.items():
        img_dir = OUT / "images" / split
        lbl_dir = OUT / "labels" / split
        img_dir.mkdir(parents=True)
        lbl_dir.mkdir(parents=True)
        n_img = n_box = n_bg = 0

        for s in sessions:
            if not (RAW / s).exists():
                print(f" [{split}] bo qua {s}: chua co anh trong {RAW / s}")
                continue
            # Lấy ảnh làm chuẩn: nhãn của ảnh đã xóa khỏi data/raw tự bị bỏ qua
            for img in sorted((RAW / s).glob("*.jpg")):
                # Ảnh chưa gán nhãn thì dừng, không ghi nhãn rỗng (YOLO sẽ hiểu là không có người)
                if img.stem not in labels:
                    sys.exit(f"{img.name} chua co nhan. Gan nhan va xuat lai zip truoc khi chay.")
                text = labels[img.stem]
                shutil.copy2(img, img_dir / img.name)
                (lbl_dir / f"{img.stem}.txt").write_text(text)
                boxes = len([line for line in text.splitlines() if line.strip()])
                n_img += 1
                n_box += boxes
                n_bg += boxes == 0      # ảnh nền: không có người

        print(f"   [{split}] {n_img} anh, {n_box} khung, {n_bg} background")

    # Không ghi "path": Ultralytics lấy thư mục chứa data.yaml làm gốc,
    # nên giải nén ở đâu (laptop hay Colab) cũng chạy được
    (OUT / "data.yaml").write_text(
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "names:\n"
        "  0: person\n"
    )

    zip_path = shutil.make_archive(str(OUT), "zip", root_dir=OUT)
    print(f"Xong: {OUT} va {zip_path}")


if __name__ == "__main__":
    main()