import gc
import os
import pytest
import torch

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_DEACTIVATE_ASYNC_LOAD"] = "1"
torch.set_num_threads(1)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass


@pytest.fixture(autouse=True)
def cleanup_memory():
    yield
    gc.collect()
