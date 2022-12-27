"""Tests for cloud_storage_mocker._core."""

import pathlib
from unittest import mock

import google.cloud.exceptions
import google.cloud.storage  # type: ignore[import]
import pytest

CopiedClient = google.cloud.storage.Client
CopiedBucket = google.cloud.storage.Bucket
CopiedBlob = google.cloud.storage.Blob

from cloud_storage_mocker import Mount, patch  # noqa: E402


def _prepare_dirs(root_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    src_dir = root_path / "src"
    dest_dir = root_path / "dest"
    src_dir.mkdir()
    dest_dir.mkdir()
    return src_dir, dest_dir


def test__blob__download_to_file__success(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with open(dest_dir / "dest.txt", "wb") as fp:
            blob.download_to_file(fp)

    assert (dest_dir / "dest.txt").read_text() == "Hello."


def test__blob__download_to_file__forbidden(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with open(dest_dir / "dest.txt", "wb") as fp:
            with pytest.raises(google.cloud.exceptions.Forbidden):
                blob.download_to_file(fp)


def test__blob__download_to_file__not_found(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with open(dest_dir / "dest.txt", "wb") as fp:
            with pytest.raises(google.cloud.exceptions.NotFound):
                blob.download_to_file(fp)


def test__blob__download_to_filename__success(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        blob.download_to_filename(str(dest_dir / "dest.txt"))

    assert (dest_dir / "dest.txt").read_text() == "Hello."


def test__blob__download_to_filename__forbidden(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.download_to_file(str(dest_dir / "dest.txt"))


def test__blob__download_to_filename__not_found(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with pytest.raises(google.cloud.exceptions.NotFound):
            blob.download_to_file(str(dest_dir / "dest.txt"))


def test__blob__download_as_bytes__success(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        assert blob.download_as_bytes() == b"Hello."


def test__blob__download_as_bytes__forbidden(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.download_as_bytes()


def test__blob__download_as_bytes__not_found(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with pytest.raises(google.cloud.exceptions.NotFound):
            blob.download_as_bytes()


def test__blob__download_as_text__success(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        assert blob.download_as_text() == "Hello."


def test__blob__download_as_text__forbidden(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("readable", src_dir)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.download_as_text()


def test__blob__download_as_text__not_found(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)

    with patch([Mount("readable", src_dir, readable=True)]):
        blob = google.cloud.storage.Client().bucket("readable").blob("src.txt")
        with pytest.raises(google.cloud.exceptions.NotFound):
            blob.download_as_text()


def test__blob__upload_from_file__success(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("writable", dest_dir, writable=True)]):
        blob = google.cloud.storage.Client().bucket("writable").blob("dest.txt")
        with open(src_dir / "src.txt", "rb") as fp:
            blob.upload_from_file(fp)

    assert (dest_dir / "dest.txt").read_text() == "Hello."


def test__blob__upload_from_file__forbidden(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("writable", dest_dir)]):
        blob = google.cloud.storage.Client().bucket("writable").blob("dest.txt")
        with open(src_dir / "src.txt", "rb") as fp:
            with pytest.raises(google.cloud.exceptions.Forbidden):
                blob.upload_from_file(fp)


def test__blob__upload_from_filename__success(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("writable", dest_dir, writable=True)]):
        blob = google.cloud.storage.Client().bucket("writable").blob("dest.txt")
        blob.upload_from_filename(str(src_dir / "src.txt"))

    assert (dest_dir / "dest.txt").read_text() == "Hello."


def test__blob__upload_from_filename__forbidden(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)
    (src_dir / "src.txt").write_text("Hello.")

    with patch([Mount("writable", dest_dir)]):
        blob = google.cloud.storage.Client().bucket("writable").blob("dest.txt")
        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.upload_from_filename(str(src_dir / "src.txt"))


def test__blob__upload_from_string__success(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)

    with patch([Mount("writable", dest_dir, writable=True)]):
        blob = google.cloud.storage.Client().bucket("writable").blob("dest.txt")
        blob.upload_from_string("Hello.")

    assert (dest_dir / "dest.txt").read_text() == "Hello."


def test__blob__upload_from_string__forbidden(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)

    with patch([Mount("writable", dest_dir)]):
        blob = google.cloud.storage.Client().bucket("writable").blob("dest.txt")
        with pytest.raises(google.cloud.exceptions.Forbidden):
            blob.upload_from_string("Hello.")


# NOTE(odashi):
# Google Cloud Storage is folder-agnostic.
# Files in a nested directory should be created without any errors.
def test__blob__upload_from_string__nested(tmp_path: pathlib.Path) -> None:
    src_dir, dest_dir = _prepare_dirs(tmp_path)

    with patch([Mount("writable", dest_dir, writable=True)]):
        blob = google.cloud.storage.Client().bucket("writable").blob("foo/bar.txt")
        blob.upload_from_string("Hello.")

    assert (dest_dir / "foo" / "bar.txt").read_text() == "Hello."


def test__copied__unpatched() -> None:
    with patch([]):
        # These are copied from the original library before patching it.
        assert not isinstance(CopiedClient, mock.MagicMock)
        assert not isinstance(CopiedBucket, mock.MagicMock)
        assert not isinstance(CopiedBlob, mock.MagicMock)


def test__copied__patched() -> None:
    with patch(
        [],
        client_cls_paths=[__name__ + ".CopiedClient"],
        bucket_cls_paths=[__name__ + ".CopiedBucket"],
        blob_cls_paths=[__name__ + ".CopiedBlob"],
    ):
        assert isinstance(CopiedClient, mock.MagicMock)
        assert isinstance(CopiedBucket, mock.MagicMock)
        assert isinstance(CopiedBlob, mock.MagicMock)
