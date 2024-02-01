"""Test for README example."""

import pathlib

import google.cloud.storage  # type: ignore[import-untyped]

from cloud_storage_mocker import BlobMetadata, Mount
from cloud_storage_mocker import patch as gcs_patch


def test_something(tmp_path: pathlib.Path) -> None:
    # Creates two temporary directories for readable/writable buckets.
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir()
    dest_dir.mkdir()

    # A sample file on the readable bucket.
    (src_dir / "hello.txt").write_text("Hello.")
    # Optionally, object metadata can also be specified by the file beside the
    # content, suffixed by ".__metadata__".
    (src_dir / "hello.txt.__metadata__").write_text(
        BlobMetadata(content_type="text/plain").dump_json()
    )

    # Mounts directories. Empty list is allowed if no actual access is required.
    with gcs_patch(
        [
            Mount("readable", src_dir, readable=True),
            Mount("writable", dest_dir, writable=True),
        ],
    ):
        client = google.cloud.storage.Client()

        # Reads a blob.
        blob = client.bucket("readable").blob("hello.txt")
        assert blob.download_as_text() == "Hello."
        # Metadata is available after downloading the content.
        assert blob.content_type == "text/plain"

        # Writes a blob.
        blob = client.bucket("writable").blob("world.txt")
        blob.upload_from_string("World.")

    # Checks if the file is written appropriately.
    assert (dest_dir / "world.txt").read_text() == "World."
