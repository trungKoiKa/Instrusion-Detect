import shutil 
import sys
import zipfile
from pathlib import Path 

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LABELS = ROOT / "data" / "labels_cvat"
OUT = ROOT / "data" / "dataset"

SPLITS = {
    "train": ["s01", "s02", "s04", "s06"],
    "val": ["s03"],
    "test": ["s05", "s07"],
}

def read_cvat_labels():
    labels = {}
    for zp in sorted(LABELS.glob("*.zip")):
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                if name.startswith("obj_train_data/") and name.endswith(".txt"):
                    stem = Path(name).stem
                    labels[stem] = z.read(name).decode()
    return labels

def main():
    labels = read_cvat_labels()
    print(f"Đọc được {len(labels)} file nhãn từ {LABELS}")

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
            for img in sorted((RAW / s).glob("*.jpg")):
                if img.stem not in labels:
                    sys.exit(f"{img.name} chua co nhan. Gan nhan va xuat lai zip truoc khi chay.")
                text = labels[img.stem]
                shutil.copy2(img, img_dir / img.name)
                (lbl_dir / f"{img.stem}.txt").write_text(text)
                boxes = len([line for line in text.splitlines() if line.strip()])
                n_img += 1
                n_box += boxes
                n_bg += boxes == 0
        print(f"   [{split}] {n_img} anh, {n_box} khung, {n_bg} background")

    (OUT / "data.yaml").write_text(
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "names: \n"
        "  0: person\n"
    )

    zip_path = shutil.make_archive(str(OUT), "zip", root_dir=OUT)
    print(f"Xong: {OUT} va {zip_path}")

if __name__ == "__main__":
    main()