"""Test for README example."""

import pathlib

import google.cloud.storage  # type: ignore[import]

from cloud_storage_mocker import Mount
from cloud_storage_mocker import patch as gcs_patch


def test_something(tmp_path: pathlib.Path) -> None:
    # Creates two temporary directories for readable/writable buckets.
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir()
    dest_dir.mkdir()

    # A sample file on the readable bucket.
    (src_dir / "hello.txt").write_text("Hello.")

    # Mounts directories.
    with gcs_patch(
        [
            Mount("readable", src_dir, readable=True),
            Mount("writable", dest_dir, writable=True),
        ],
    ):
        # Reads a blob.
        blob = google.cloud.storage.Client().bucket("readable").blob("hello.txt")
        assert blob.download_as_text() == "Hello."

        # Writes a blob.
        blob = google.cloud.storage.Client().bucket("writable").blob("world.txt")
        blob.upload_from_string("World.")

    # Checks if the file is written appropriately.
    assert (dest_dir / "world.txt").read_text() == "World."
