# cloud-storage-mocker

Mocker library of Google Cloud Storage with local filesystem mounting.


## Getting started

This library provides `patch` context manager, which replaces following classes on the
`google-cloud-storage` package:

- `Client`
- `Bucket`
- `Blob`

`patch` takes a list of `Mount` objects, which represents a mapping between a bucket
name and a local storage.
Each mount has Boolean configs `readable` and `writable` to control read/write access
to the mounted bucket.

A canonical way to use this library is writing unit tests that are working with Google
Cloud Storage:

```python
import tempfile

import google.cloud.storage

from cloud_storage_mocker import patch as gcs_patch, Mount

# A pytest test case.
def test_something() -> None:
    # Creates a temporary directory
    # And mounts it to the Cloud Storage bucket "my_bucket"
    with (
        tempfile.TemporaryDirectory() as readable_dir,
        tempfile.TemporaryDirectory() as writable_dir,
        gcs_patch([
            Mount("readable_bucket", readable_dir, readable=True),
            Mount("writable_bucket", writable_dir, writable=True),
        ]),
    ):
        # Reads a blob.
        with open(readable_dir + "/test.txt", "w") as fp:
            fp.write("Hello.")
        blob = google.cloud.storage.Client().bucket("readable_bucket").blob("test.txt")
        assert readable_blob.download_as_text() == "Hello."

        # Writes a blob.
        blob = google.cloud.storage.Client().bucket("writable_bucket").blob("test.txt")
        blob.upload_from_string("World.")
        with open(writable_dir + "/test.txt") as fp:
            assert fp.read() == "World."
```


## Patched methods

Methods below has a specialized behavior to mount the local filesystem.

Other methods are mapped to `MagicMock`.

- `Client()`
- `Client.bucket()`
- `Bucket.blob()`
- `Blob.download_as_text()`
- `Blob.upload_from_string()`


## Caution

This library is provided for writing unit tests that work with the Google Cloud Storage
client library. DO NOT use this library on any code on the production.
