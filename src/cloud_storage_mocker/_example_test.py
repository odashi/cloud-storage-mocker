"""Test for README example."""

import tempfile

import google.cloud.storage  # type: ignore[import]

from cloud_storage_mocker import Mount
from cloud_storage_mocker import patch as gcs_patch


def test_something() -> None:
    # Creates a temporary directory
    # And mounts it to the Cloud Storage bucket "my_bucket"
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        tempfile.TemporaryDirectory() as writable_dir,
        gcs_patch(
            [
                Mount("readable_bucket", readable_dir, readable=True),
                Mount("writable_bucket", writable_dir, writable=True),
            ]
        ),
    ):
        # Reads a blob.
        with open(readable_dir + "/test.txt", "w") as fp:
            fp.write("Hello.")
        blob = google.cloud.storage.Client().bucket("readable_bucket").blob("test.txt")
        assert blob.download_as_text() == "Hello."

        # Writes a blob.
        blob = google.cloud.storage.Client().bucket("writable_bucket").blob("test.txt")
        blob.upload_from_string("World.")
        with open(writable_dir + "/test.txt") as fp:
            assert fp.read() == "World."
