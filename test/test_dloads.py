from pathlib import Path
from tempfile import TemporaryDirectory

from chellow.dloads import SERIAL_DIGITS, open_file, startup


def test_startup():
    with TemporaryDirectory() as tmpdir:
        startup(Path(tmpdir), run_deleter=False)


def test_startup_interrupted():
    with TemporaryDirectory() as tempdir:
        tmpdir = Path(tempdir)
        downloads = tmpdir / "downloads"
        downloads.mkdir()
        fname = "0" * SERIAL_DIGITS + "_RUNNING_inewton.ods"
        (downloads / fname).touch()
        startup(tmpdir, run_deleter=False)


def test_truncate():
    with TemporaryDirectory() as tmpdir:
        startup(Path(tmpdir), run_deleter=False)
        user = None
        with open_file("test.txt", user, mode="w") as fl:
            fl.truncate()
