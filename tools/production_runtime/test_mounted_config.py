from pathlib import Path
import shutil
import pytest
from tools.production_runtime.mounted_config import FILES, materialize_render_configuration


def test_provider_mount_symlinks_become_private_regular_files(tmp_path):
    mount = tmp_path / 'mount'
    mount.mkdir()
    env = {}
    for key, name in FILES.items():
        source = tmp_path / name
        source.write_text('synthetic configuration')
        (mount / name).symlink_to(source)
        env[key] = str(mount / name)
    directory = materialize_render_configuration(env, mount_root=mount)
    try:
        assert directory.stat().st_mode & 0o777 == 0o700
        for key in FILES:
            p = Path(env[key])
            assert not p.is_symlink()
            assert p.read_text() == 'synthetic configuration'
            assert p.stat().st_mode & 0o777 == 0o600
    finally:
        shutil.rmtree(directory)


def test_mount_scope_cannot_include_an_unapproved_file(tmp_path):
    env = {k: str(tmp_path / n) for k, n in FILES.items()}
    env['WNC_PRODUCTION_MANIFEST'] = str(tmp_path / 'other.json')
    with pytest.raises(ValueError, match='mount_scope_mismatch'):
        materialize_render_configuration(env, mount_root=tmp_path)


def test_mount_read_failure_leaves_environment_unchanged(tmp_path):
    env = {k: str(tmp_path / n) for k, n in FILES.items()}
    original = dict(env)
    with pytest.raises(ValueError, match='mount_unavailable'):
        materialize_render_configuration(env, mount_root=tmp_path)
    assert env == original
