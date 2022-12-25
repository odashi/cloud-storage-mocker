"""cloud_storage_mocker root package."""

try:
    from cloud_storage_mocker import _version

    __version__ = _version.__version__
except Exception:
    __version__ = ""
