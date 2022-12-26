"""Core implementation."""

import contextlib
import dataclasses
import pathlib
from collections.abc import Iterator, Sequence
from typing import Any, final
from unittest import mock

import google.cloud.exceptions
import google.cloud.storage  # type: ignore[import]

# Obtains original objects before mocking.
_ORIG_CLIENT = google.cloud.storage.Client
_ORIG_BUCKET = google.cloud.storage.Bucket
_ORIG_BLOB = google.cloud.storage.Blob


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
    directory: str
    readable: bool = False
    writable: bool = False


class Environment:
    """environment for Cloud Storage."""

    _mounts: Sequence[Mount]

    def __init__(self, mounts: Sequence[Mount]) -> None:
        """Initializer.

        Args:
            mounts: List of mount configs.
        """
        self._mounts = mounts

    def get_mount(self, bucket_name: str) -> Mount:
        """Obtains the mount config corresponding to the bucket.

        Args:
            bucket_name: Bucket name.

        Returns:
            Mount object corresponding to `bucket_name`.

        Raises:
            NotFound: No mount config for `bucket_name`.
        """
        for m in self._mounts:
            if m.bucket_name == bucket_name:
                return m

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
        self._bucket = bucket
        self._name = name

    @property
    def _env(self) -> Environment:
        """Returns the environment of this client."""
        return self._bucket._env

    def _get_local_path(self, mount: Mount) -> pathlib.Path:
        """Returns the local path of this blob."""
        return pathlib.Path(f"{mount.directory}/{self._name}")

    def _get_gs_path(self) -> str:
        """Returns the Cloud Storage path of this blob."""
        return f"gs://{self._bucket.name}/{self._name}"

    def download_as_text(
        self,
        *args: Any,  # Not supported
    ) -> str:
        """Downloads blob as a string."""
        mount = self._env.get_mount(self._bucket.name)
        if not mount.readable:
            raise google.cloud.exceptions.Forbidden(  # type: ignore[no-untyped-call]
                f"Bucket is not readable: {self._bucket.name}"
            )

        local_path = self._get_local_path(mount)

        try:
            with local_path.open("r") as fp:
                return fp.read()
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )

    def upload_from_string(
        self,
        data: str | bytes,
        *args: Any,  # Not supported
    ) -> None:
        """Uploads string to a blob."""
        mount = self._env.get_mount(self._bucket.name)
        if not mount.writable:
            raise google.cloud.exceptions.Forbidden(  # type: ignore[no-untyped-call]
                f"Bucket is not writable: {self._bucket.name}"
            )

        local_path = self._get_local_path(mount)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if isinstance(data, str):
                with local_path.open("w") as fp:
                    fp.write(data)
            else:
                with local_path.open("wb") as fp:
                    fp.write(data)
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )


@contextlib.contextmanager
def patch(mounts: Sequence[Mount]) -> Iterator[None]:
    """Patch Cloud Storage library.

    Args:
        mounts: List of mount configs. See also Environment.
    """
    env = Environment(mounts)
    with mock.patch("google.cloud.storage.Client") as mock_client:
        mock_client.side_effect = lambda *args: Client(*args, _env=env)
        yield
