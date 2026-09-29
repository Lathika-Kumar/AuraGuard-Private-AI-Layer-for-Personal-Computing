import gc
import os
import pytest

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


@pytest.fixture(autouse=True)
def cleanup_memory():
    yield
    gc.collect()
