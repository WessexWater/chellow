from pathlib import Path
from tempfile import TemporaryDirectory

from chellow.dloads import open_file, startup


def test_startup(mocker):
    mocker.patch("chellow.dloads.FileDeleter")
    with TemporaryDirectory() as tmpdir:
        startup(Path(tmpdir))


def test_truncate(mocker):
    mocker.patch("chellow.dloads.FileDeleter")
    with TemporaryDirectory() as tmpdir:
        startup(Path(tmpdir))
        user = None
        with open_file("test.txt", user, mode="w") as fl:
            fl.truncate()
