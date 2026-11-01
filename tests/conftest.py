import pytest

from src.data.repository import load_dataset


@pytest.fixture(scope="session")
def dataset():
    return load_dataset()

