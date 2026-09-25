import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('canonical_package', ROOT / 'scripts/agent/build_portal_package.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_crlf_and_lf_package_identically_without_rewriting_source(tmp_path):
    source = tmp_path / 'requirements.txt'
    source.write_bytes(b'example\r\n')
    assert builder.canonical_bytes(source) == b'example\n'
    assert source.read_bytes() == b'example\r\n'


def test_canonicalization_preserves_trailing_newline_and_unicode(tmp_path):
    source = tmp_path / 'main.py'
    payload = '# Oñati\n\n'.encode('utf-8')
    source.write_bytes(payload)
    assert builder.canonical_bytes(source) == payload


def test_unknown_encoding_is_rejected(tmp_path):
    import pytest
    source = tmp_path / 'main.py'
    source.write_bytes(b'\xff')
    with pytest.raises(UnicodeDecodeError):
        builder.canonical_bytes(source)
