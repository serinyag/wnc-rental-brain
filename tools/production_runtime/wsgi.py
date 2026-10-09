"""Production-only WSGI entry point; gunicorn binds loopback behind Entra proxy."""
import os
from tools.phase_08_workflow.test_console import build_test_console_app
if os.environ.get('APP_ENV')!='production':
    raise RuntimeError('production_environment_required')
application=build_test_console_app()
