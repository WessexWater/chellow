from pathlib import Path
from tempfile import TemporaryDirectory

from chellow.dloads import startup


def test_startup(mocker):
    mocker.patch("chellow.dloads.FileDeleter")
    with TemporaryDirectory() as tmpdir:
        startup(Path(tmpdir))
