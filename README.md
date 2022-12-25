# cloud-storage-mocker

Mocker library of Google Cloud Storage with local filesystem mounting.


## Install

For package users:

```shell
pip install cloud-storage-mocker
```

For package developers:

```shell
git clone git@github.com:odashi/cloud-storage-mocker
cd cloud-storage-mocker
python -m venv venv
source venv/bin/activate
pip install -e '.[dev]'
```


## How the package works

This library provides `patch` context manager, which replaces following classes on the
`google-cloud-storage` package:

- `Client`
- `Bucket`
- `Blob`

`patch` takes a list of `Mount` objects, which represent mappings between bucket names
and directories on the local filesystem.
Each `Mount` has Boolean configs `readable` and `writable` to control read/write
permissions to the mounted buckets.

A canonical use-case of this package is writing unit tests to check the behavior of the
code that works with Google Cloud Storage:

```python
import tempfile

import google.cloud.storage  # type: ignore[import]

from cloud_storage_mocker import Mount
from cloud_storage_mocker import patch as gcs_patch


def test_something() -> None:
    # Creates two temporary directories, and mount them as readable/writable buckets.
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
```


## Patched methods

Methods listed below have specialized behavior to mount the local filesystem.

Other methods are mapped to `MagicMock`.

- `Client()`
- `Client.bucket()`
- `Bucket.blob()`
- `Blob.download_as_text()`
- `Blob.upload_from_string()`


## Caution

This library is basically provided for writing unit tests.
DO NOT use this library on any code on the production.
