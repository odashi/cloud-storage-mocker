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
```


## Patched methods

Methods listed below have specialized behavior to mount the local filesystem.

Other methods are mapped to `MagicMock`.

- `Client()`
- `Client.bucket()`
- `Bucket()`
- `Bucket.blob()`
- `Blob()`
- `Blob.download_to_file()`
- `Blob.download_to_filename()`
- `Blob.download_as_bytes()`
- `Blob.download_as_text()`
- `Blob.upload_from_file()`
- `Blob.upload_from_filename()`
- `Blob.upload_from_string()`


## Caution

This library is basically provided for writing unit tests.
DO NOT use this library on any code on the production.
