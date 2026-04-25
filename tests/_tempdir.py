import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path


TEST_TEMP_ROOT = Path(__file__).resolve().parent / ".tmp"
TEST_TEMP_ROOT.mkdir(exist_ok=True)


@contextmanager
def managed_tempdir():
    temp_dir = TEST_TEMP_ROOT / f"tmp_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield str(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
