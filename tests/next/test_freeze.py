import subprocess
import pytest
from pathlib import Path
from scripts.ops import verify_runtime_identity as identity

@pytest.mark.parametrize('target', ['agentes/gipuzkoa360/main.py', 'agentes/gipuzkoa360/tools.py',
                                  'agentes/gipuzkoa360/portal/main.py'])
def test_missing_or_changed_byte_fails_without_touching_runtime(tmp_path, monkeypatch, target):
    expected={p:subprocess.check_output(['git','show',f'{identity.RUNTIME}:{p}'],cwd=identity.ROOT) for p in identity.frozen_files()}
    for name,blob in expected.items():
        path=tmp_path/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(blob)
    original=subprocess.check_output
    def fake_git(args, **kwargs):
        kwargs['cwd']=identity.ROOT
        return original(args, **kwargs)
    monkeypatch.setattr(subprocess,'check_output',fake_git)
    assert identity.audit(tmp_path)['status']=='PASS'
    path=tmp_path/target
    path.write_bytes(path.read_bytes()+b'\n')
    assert identity.audit(tmp_path)['status']=='FAIL'
    path.unlink()
    assert identity.audit(tmp_path)['status']=='FAIL'
