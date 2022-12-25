"""Core implementation."""

import contextlib
import dataclasses
import pathlib
from collections.abc import Iterator, Sequence
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

    def client(self) -> "Client":
        """Creates a mock client object."""
        return Client(self)


class Client(mock.MagicMock):
    """Mocked class for Cloud Storage client."""

    _env: Environment

    def __init__(self, env: Environment) -> None:
        """Initializer."""
        super().__init__(_ORIG_CLIENT)
        self._env = env

    def bucket(self, name: str) -> "Bucket":
        """Creates a mock bucket object."""
        return Bucket(self._env, name)


class Bucket(mock.MagicMock):
    """Mocked object for Cloud Storage bucket."""

    _env: Environment
    _name: str

    def __init__(self, env: Environment, name: str) -> None:
        """Initializer."""
        super().__init__(_ORIG_BUCKET)
        self._env = env
        self._name = name

    def blob(self, path: str) -> "Blob":
        """Creates a new mock blob object."""
        return Blob(self._env, self._name, path)


class Blob(mock.MagicMock):
    """Mocked object for Cloud Storage blob."""

    _env: Environment
    _bucket: str
    _path: str

    def __init__(self, env: Environment, bucket: str, path: str) -> None:
        """Initializer."""
        super().__init__(_ORIG_BLOB)
        self._env = env
        self._bucket = bucket
        self._path = path

    def _get_local_path(self, mount: Mount) -> pathlib.Path:
        return pathlib.Path(f"{mount.directory}/{self._path}")

    def _get_gs_path(self) -> str:
        return f"gs://{self._bucket}/{self._path}"

    def download_as_text(self) -> str:
        mount = self._env.get_mount(self._bucket)
        if not mount.readable:
            raise google.cloud.exceptions.Forbidden(  # type: ignore[no-untyped-call]
                f"Bucket is not readable: {self._bucket}"
            )

        local_path = self._get_local_path(mount)

        try:
            with local_path.open("r") as fp:
                return fp.read()
        except FileNotFoundError:
            raise google.cloud.exceptions.NotFound(  # type: ignore[no-untyped-call]
                f"File not found: {self._get_gs_path()} -> {local_path}"
            )

    def upload_from_string(self, data: str | bytes) -> None:
        mount = self._env.get_mount(self._bucket)
        if not mount.writable:
            raise google.cloud.exceptions.Forbidden(  # type: ignore[no-untyped-call]
                f"Bucket is not writable: {self._bucket}"
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
        mock_client.side_effect = env.client
        yield
