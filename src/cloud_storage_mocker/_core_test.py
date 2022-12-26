"""Tests for cloud_storage_mocker._core."""

import pathlib
import tempfile

import google.cloud.exceptions
import google.cloud.storage  # type: ignore[import]
import pytest

from cloud_storage_mocker import Mount, patch


def test__blob__download_to_file__success() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, readable=True)]),
    ):
        dir = pathlib.Path(readable_dir)
        (dir / "test.txt").write_text("Hello.")

        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with open(dir / "copied.txt", "wb") as fp:
            blob.download_to_file(fp)

        with open(dir / "copied.txt") as fp:
            assert fp.read() == "Hello."


def test__blob__download_to_file__forbidden() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir)]),
    ):
        dir = pathlib.Path(readable_dir)
        (dir / "test.txt").write_text("Hello.")

        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with open(dir / "copied.txt", "wb") as fp:
            with pytest.raises(google.cloud.exceptions.Forbidden):
                blob.download_to_file(fp)


def test__blob__download_to_file__not_found() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, readable=True)]),
    ):
        dir = pathlib.Path(readable_dir)

        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with open(dir / "copied.txt", "wb") as fp:
            with pytest.raises(google.cloud.exceptions.NotFound):
                blob.download_to_file(fp)


def test__blob__download_as_bytes__success() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, readable=True)]),
    ):
        dir = pathlib.Path(readable_dir)
        (dir / "test.txt").write_text("Hello.")

        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        assert blob.download_as_bytes() == b"Hello."


def test__blob__download_as_bytes__forbidden() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir)]),
    ):
        dir = pathlib.Path(readable_dir)
        (dir / "test.txt").write_text("Hello.")

        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.download_as_bytes()


def test__blob__download_as_bytes__not_found() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, readable=True)]),
    ):
        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with pytest.raises(google.cloud.exceptions.NotFound):
            blob.download_as_bytes()


def test__blob__download_as_text__success() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, readable=True)]),
    ):
        dir = pathlib.Path(readable_dir)
        (dir / "test.txt").write_text("Hello.")

        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        assert blob.download_as_text() == "Hello."


def test__blob__download_as_text__forbidden() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir)]),
    ):
        dir = pathlib.Path(readable_dir)
        (dir / "test.txt").write_text("Hello.")

        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.download_as_text()


def test__blob__download_as_text__not_found() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, readable=True)]),
    ):
        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with pytest.raises(google.cloud.exceptions.NotFound):
            blob.download_as_text()


def test__blob__upload_from_string__success() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, writable=True)]),
    ):
        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")
        blob.upload_from_string("Hello.")

        dir = pathlib.Path(readable_dir)
        assert (dir / "test.txt").read_text() == "Hello."


def test__blob__upload_from_string__forbidden() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir)]),
    ):
        blob = google.cloud.storage.Client().bucket("readable").blob("test.txt")

        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.upload_from_string("Hello.")


# NOTE(odashi):
# Google Cloud Storage is folder-agnostic.
# Files in a nested directory should be created without any errors.
def test__blob__upload_from_string__nested() -> None:
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        patch([Mount("readable", readable_dir, writable=True)]),
    ):
        blob = google.cloud.storage.Client().bucket("readable").blob("foo/bar.txt")
        blob.upload_from_string("Hello.")

        dir = pathlib.Path(readable_dir)
        assert (dir / "foo" / "bar.txt").read_text() == "Hello."
