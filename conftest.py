import pytest


@pytest.fixture(autouse=True)
def use_tmp_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"
