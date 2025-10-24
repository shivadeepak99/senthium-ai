def test_import_src_package():
    """Smoke test: import the src package to execute `src/__init__.py`."""
    import importlib
    src = importlib.import_module('src')
    assert hasattr(src, '__version__')
    assert src.__version__ != ''
