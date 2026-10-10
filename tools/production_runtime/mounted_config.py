"""Copy the four approved Render config mounts into private regular files.

Render owns the read-only mount and its symlink layout. The application keeps
its strict regular-file contract; credentials remain environment variables.
"""
import atexit
import os
from pathlib import Path
import shutil
import tempfile

FILES = {
    'WNC_PRODUCTION_MANIFEST': 'production-manifest.json',
    'WNC_PRODUCTION_CONTROLS': 'controls.json',
    'WNC_PRODUCTION_OPERATORS': 'operators.json',
    'WNC_OAUTH_PROXY_CONFIG': 'oauth2-proxy.cfg',
}


def materialize_render_configuration(env=None, *, mount_root=Path('/etc/secrets')):
    env = os.environ if env is None else env
    if not any(str(env.get(k, '')).startswith(str(mount_root) + '/') for k in FILES):
        return None
    if any(env.get(k) != str(mount_root / name) for k, name in FILES.items()):
        raise ValueError('production_config_mount_scope_mismatch')
    destination = Path(tempfile.mkdtemp(prefix='wnc-production-config-'))
    try:
        for key, name in FILES.items():
            with (mount_root / name).open('rb') as source:
                payload = source.read(1024 * 1024 + 1)
            if not payload or len(payload) > 1024 * 1024:
                raise ValueError('production_config_mount_size_invalid')
            fd = os.open(destination / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as target:
                target.write(payload)
        for key, name in FILES.items():
            env[key] = str(destination / name)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise ValueError('production_config_mount_unavailable') from None
    atexit.register(shutil.rmtree, destination, ignore_errors=True)
    return destination
