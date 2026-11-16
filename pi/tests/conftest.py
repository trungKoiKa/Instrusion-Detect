# cho phép 'import safecam' khi chạy 'pytest pt/tests' từ gốc repo
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

