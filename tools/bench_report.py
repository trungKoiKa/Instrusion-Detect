"""Tóm tắt file CSV của bench_pi.py và vẽ biểu đồ cho báo cáo.

Chạy: python tools/bench_report.py logs/bench_xxx.csv
Ra: bảng tóm tắt in trên màn hình + file .png cạnh file CSV.
"""
import csv
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")              # vẽ ra file, không cần mở cửa sổ
import matplotlib.pyplot as plt


def column(rows, name):
    """Lấy một cột thành danh sách số, bỏ ô trống."""
    return [float(r[name]) for r in rows if r[name] != ""]


def percentile(values, p):
    """Phân vị p% (ví dụ p=5: 5% số giây có FPS thấp hơn giá trị này)."""
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main():
    if len(sys.argv) != 2:
        sys.exit("Dùng: python tools/bench_report.py logs/bench_xxx.csv")
    path = Path(sys.argv[1])
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    minutes = [float(r["elapsed_s"]) / 60 for r in rows]
    fps = column(rows, "fps")
    infer = column(rows, "infer_ms")
    cpu = column(rows, "cpu_percent")
    ram = column(rows, "ram_used_mb")
    temp = column(rows, "temp_c")
    throttled = [r["throttled"] for r in rows if r["throttled"]]
    bi_ha_xung = any(int(t, 16) != 0 for t in throttled)

    # Bảng Markdown: dán thẳng vào báo cáo hoặc Word
    print("| Chỉ số | Giá trị |")
    print("| --- | --- |")
    print(f"| Thời gian đo | {minutes[-1]:.1f} phút ({len(rows)} giây có số liệu) |")
    print(f"| FPS trung bình | {statistics.mean(fps):.2f} |")
    print(f"| FPS thấp nhất | {min(fps):.2f} |")
    print(f"| FPS phân vị 5% | {percentile(fps, 5):.2f} |")
    print(f"| Thời gian YOLO trung bình / p95 | {statistics.mean(infer):.0f} / {percentile(infer, 95):.0f} ms |")
    print(f"| CPU trung bình | {statistics.mean(cpu):.0f} % |")
    print(f"| RAM dùng lớn nhất | {max(ram):.0f} MB |")
    if temp:
        print(f"| Nhiệt độ trung bình / cao nhất | {statistics.mean(temp):.1f} / {max(temp):.1f} °C |")
    print(f"| Hạ xung | {'CÓ' if bi_ha_xung else 'không'} |")

    # Biểu đồ 3 tầng: FPS, nhiệt độ, CPU theo thời gian
    fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    for ax, name, label in [(axes[0], "fps", "FPS"),
                            (axes[1], "temp_c", "Nhiệt độ (°C)"),
                            (axes[2], "cpu_percent", "CPU (%)")]:
        xs = [m for m, r in zip(minutes, rows) if r[name] != ""]
        ys = column(rows, name)
        ax.plot(xs, ys, linewidth=1)
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
    axes[-1].set_xlabel("Thời gian (phút)")
    fig.suptitle("YOLO11n NCNN 320 px trên Raspberry Pi 4")
    fig.tight_layout()
    out = path.with_suffix(".png")
    fig.savefig(out, dpi=150)
    print(f"\nĐã lưu biểu đồ: {out}")


if __name__ == "__main__":
    main()  