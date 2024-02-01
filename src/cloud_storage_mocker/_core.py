"""Core implementation."""

import contextlib
import dataclasses
import io
import json
import os
import pathlib
import warnings
from collections.abc import Iterator, Sequence
from typing import Any, final
from unittest import mock

import google.cloud.exceptions
import google.cloud.storage  # type: ignore[import-untyped]

# Obtains original objects before mocking.
_ORIG_CLIENT = google.cloud.storage.Client
_ORIG_BUCKET = google.cloud.storage.Bucket
_ORIG_BLOB = google.cloud.storage.Blob

# Metadata could be stored on "foo/bar.baz.__metadata__"
_METADATA_EXTENSION = "__metadata__"


@dataclasses.dataclass(frozen=True)
class BlobMetadata:
    """Metadata of a blob."""

    # HTTP headers
    cache_control: str | None = None
    content_disposition: str | None = None
    content_encoding: str | None = None
    content_language: str | None = None
    content_type: str | None = None

    def dump_json(self) -> str:
        """Dumps JSON representation of this object."""
        return json.dumps(dataclasses.asdict(self))


@dataclasses.dataclass(frozen=True)
class Mount:
    """Mount configs for mock Cloud Storage.

    Attributes:
        bucket_name: Bucket name to map.
        directory: Path to the local directory to map.
        readable: True to enable read access, False to deny it.
        writable: True to enable write access, False to deny it.
    """

    bucket_name: str
    directory: pathlib.Path
    readable: bool
    writable: bool

    def __init__(
        self,
        bucket_name: str,
        directory: str | os.PathLike[str],
        readable: bool = False,
        writable: bool = False,
    ) -> None:
        object.__setattr__(self, "bucket_name", bucket_name)
        object.__setattr__(self, "directory", pathlib.Path(directory))
        object.__setattr__(self, "readable", readable)
        object.__setattr__(self, "writable", writable)


class Environment:
    """environment for Cloud Storage."""

    _mounts: dict[str, Mount]

    def __init__(self, mounts: Sequence[Mount]) -> None:
        """Initializer.

        Args:
            mounts: List of mount configs.
        """
        self._mounts = {m.bucket_name: m for m in mounts}

    def get_mount(self, bucket_name: str) -> Mount:
        """Obtains the mount config corresponding to the bucket.

        Args:
            bucket_name: Bucket name.

        Returns:
            Mount object corresponding to `bucket_name`.

        Raises:
            NotFound: No mount config for `bucket_name`.
        """
        try:
            return self._mounts[bucket_name]
        except KeyError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"No mount specified for the bucket: {bucket_name}"
            )


@final
class NoProjectMarker:
    pass


_NO_PROJECT_MARKER = NoProjectMarker()


class Client(mock.MagicMock):
    """Mocked class for Cloud Storage client."""

    _env_val: Environment

    def __init__(
        self,
        project: Any = _NO_PROJECT_MARKER,  # Not supported
        credentials: Any = None,  # Not supported
        _http: Any = None,  # Not supported
        client_info: Any = None,  # Not supported
        client_options: Any = None,  # Not supported
        use_auth_w_custom_endpoint: bool = True,  # Not supported
        *,
        _env: Environment,
    ) -> None:
        """Initializer."""
        super().__init__(_ORIG_CLIENT)
        self._env_val = _env

    @property
    def _env(self) -> Environment:
        """Returns the environment of this client."""
        return self._env_val

    def bucket(
        self,
        bucket_name: str,
        user_project: str | None = None,
    ) -> "Bucket":
        """Creates a mock bucket object."""
        return Bucket(client=self, name=bucket_name, user_project=user_project)


class Bucket(mock.MagicMock):
    """Mocked object for Cloud Storage bucket."""

    _client: Client
    name: str  # Exposed

    def __init__(
        self,
        client: Client,
        name: str,
        user_project: str | None = None,  # Not supported
    ) -> None:
        """Initializer."""
        super().__init__(_ORIG_BUCKET)
        self._client = client
        self.name = name

    @property
    def _env(self) -> Environment:
        """Returns the environment of this client."""
        return self._client._env

    def blob(
        self,
        blob_name: str,
        chunk_size: int | None = None,
        encryption_key: bytes | None = None,
        kms_key_name: str | None = None,
        generation: int | None = None,
    ) -> "Blob":
        """Creates a new mock blob object."""
        return Blob(
            name=blob_name,
            bucket=self,
            chunk_size=chunk_size,
            encryption_key=encryption_key,
            kms_key_name=kms_key_name,
            generation=generation,
        )


class Blob(mock.MagicMock):
    """Mocked object for Cloud Storage blob."""

    name: str  # Exposed
    _bucket: Bucket
    _metadata: BlobMetadata

    def __init__(
        self,
        name: str,
        bucket: Bucket,
        chunk_size: int | None = None,  # Not supported
        encryption_key: bytes | None = None,  # Not supported
        kms_key_name: str | None = None,  # Not supported
        generation: int | None = None,  # Not supported
    ) -> None:
        """Initializer."""
        super().__init__(_ORIG_BLOB)
        self.name = name
        self._bucket = bucket
        self._metadata = BlobMetadata()

    @property
    def _env(self) -> Environment:
        """Returns the environment of this client."""
        return self._bucket._env

    @property
    def cache_control(self) -> str | None:
        """Returns the HTTP Cache-Control header."""
        return self._metadata.cache_control

    @property
    def content_disposition(self) -> str | None:
        """Returns the HTTP Content-Disposition header."""
        return self._metadata.content_disposition

    @property
    def content_encoding(self) -> str | None:
        """Returns the HTTP Content-Encoding header."""
        return self._metadata.content_encoding

    @property
    def content_language(self) -> str | None:
        """Returns the HTTP Content-Language header."""
        return self._metadata.content_language

    @property
    def content_type(self) -> str | None:
        """Returns the HTTP Content-Type header."""
        return self._metadata.content_type

    def _get_local_path(
        self, readable: bool = False, writable: bool = False
    ) -> pathlib.Path:
        """Returns the local path of this blob."""
        mount = self._env.get_mount(self._bucket.name)

        if readable and not mount.readable:
            raise google.cloud.exceptions.Forbidden(  # type: ignore[no-untyped-call]
                f"Bucket is not readable: {self._bucket.name}"
            )
        if writable and not mount.writable:
            raise google.cloud.exceptions.Forbidden(  # type: ignore[no-untyped-call]
                f"Bucket is not writable: {self._bucket.name}"
            )

        return mount.directory / self.name

    def _get_gs_path(self) -> str:
        """Returns the Cloud Storage path of this blob."""
        return f"gs://{self._bucket.name}/{self.name}"

    def _update_metadata(self, local_path: pathlib.Path) -> None:
        """Updates inner metadata.

        Args:
            local_path: Path to the local file.
        """
        metadata_path = local_path.parent / f"{local_path.name}.{_METADATA_EXTENSION}"
        if not metadata_path.exists():
            return

        with metadata_path.open() as fp:
            self._metadata = BlobMetadata(**json.load(fp))

    def download_to_file(
        self,
        file_obj: io.BufferedWriter,
        *args: Any,  # Not supported
    ) -> None:
        """Downloads blob to a file object."""
        local_path = self._get_local_path(readable=True)

        try:
            with local_path.open("rb") as fp:
                data = fp.read()
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )

        file_obj.write(data)
        self._update_metadata(local_path)

    def download_to_filename(
        self,
        filename: str,
        *args: Any,  # Not supported
    ) -> None:
        """Downloads blob to a file specified by a path."""
        with open(filename, "wb") as fp:
            self.download_to_file(fp, *args)

    def download_as_bytes(
        self,
        *args: Any,  # Not supported
    ) -> bytes:
        """Downloads blob as a byte array."""
        local_path = self._get_local_path(readable=True)

        try:
            with local_path.open("rb") as fp:
                data = fp.read()
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )

        self._update_metadata(local_path)
        return data

    def download_as_string(
        self,
        *args: Any,  # Not supported
    ) -> bytes:
        """DEPRECATED: use download_as_bytes."""
        warnings.warn("Use Blob.download_as_bytes.", DeprecationWarning)
        return self.download_as_bytes(*args)

    def download_as_text(
        self,
        *args: Any,  # Not supported
    ) -> str:
        """Downloads blob as a string."""
        local_path = self._get_local_path(readable=True)

        try:
            with local_path.open("r") as fp:
                data = fp.read()
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )

        self._update_metadata(local_path)
        return data

    def upload_from_file(
        self,
        file_obj: io.BufferedReader,
        *args: Any,  # Not supported
    ) -> None:
        """Uploads the content in the opened file to a blob."""
        local_path = self._get_local_path(writable=True)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        data = file_obj.read()

        try:
            with local_path.open("wb") as fp:
                fp.write(data)
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )

    def upload_from_filename(
        self,
        filename: str,
        *args: Any,  # Not supported
    ) -> None:
        """Uploads the content in the specified file to a blob."""
        with open(filename, "rb") as fp:
            self.upload_from_file(fp)

    def upload_from_string(
        self,
        data: str | bytes,
        *args: Any,  # Not supported
    ) -> None:
        """Uploads string to a blob."""
        local_path = self._get_local_path(writable=True)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if isinstance(data, str):
                with local_path.open("w") as fp:  # fp is TextIOWrapper
                    fp.write(data)
            else:
                with local_path.open("wb") as fp:  # fp is BufferedWriter
                    fp.write(data)
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )


@contextlib.contextmanager
def patch(
    mounts: Sequence[Mount],
    client_cls_names: Sequence[str] | None = None,
    bucket_cls_names: Sequence[str] | None = None,
    blob_cls_names: Sequence[str] | None = None,
) -> Iterator[None]:
    """Patch Cloud Storage library.

    Args:
        mounts: List of mount configs. See also Environment.
        client_cls_names: List of fully qualified names that will be patched by the
            mocked Client class.
        bucket_cls_names: List of fully qualified names that will be patched by the
            mocked Bucket class.
        blob_cls_names: List of fully qualified names that will be patched by the mocked
            Blob class.
    """
    client_cls_names = list(client_cls_names or []) + ["google.cloud.storage.Client"]
    bucket_cls_names = list(bucket_cls_names or []) + ["google.cloud.storage.Bucket"]
    blob_cls_names = list(blob_cls_names or []) + ["google.cloud.storage.Blob"]

    env = Environment(mounts)

    with contextlib.ExitStack() as stack:
        for name in client_cls_names:
            mocked = stack.enter_context(mock.patch(name))
            mocked.side_effect = lambda *args, **kwargs: Client(
                *args, _env=env, **kwargs
            )

        for name in bucket_cls_names:
            mocked = stack.enter_context(mock.patch(name))
            mocked.side_effect = lambda *args, **kwargs: Bucket(*args, **kwargs)

        for name in blob_cls_names:
            mocked = stack.enter_context(mock.patch(name))
            mocked.side_effect = lambda *args, **kwargs: Blob(*args, **kwargs)

        yield
