"""One durable-disk pilot instance: auth proxy, app and independent monitor.

Any child failure closes every provider lane and terminates the service. No lane
can be enabled here. Render restart therefore always returns to all-off.
"""
import os,signal,subprocess,sys,time
from pathlib import Path
from .config import ProductionContract,LANES
from .alerts import atomic_json,emit

def main():
    from .mounted_config import materialize_render_configuration
    materialize_render_configuration()
    c=ProductionContract.from_env()
    from . import state_store
    if state_store.enabled(c):state_store.disable(c)
    c.validate(os.environ,initial=True)
    c.verify_baseline(Path(__file__).resolve().parents[2])
    for name in ('spool_path','lifecycle_spool_path'):
        p=Path(c.manifest['alerting'][name]);p.mkdir(parents=True,exist_ok=True,mode=0o700)
    children=[]
    def stop(*_):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        heartbeat=Path(c.manifest['alerting']['spool_path'])/'heartbeat.state'
        heartbeat.unlink(missing_ok=True)
        emit(c,'MONITOR_READY')
        children.append(subprocess.Popen([sys.executable,'-m','tools.production_runtime.monitor_worker']))
        deadline=time.time()+30
        while not heartbeat.exists():
            if children[0].poll() is not None or time.time()>deadline:raise RuntimeError('monitor_startup_failed')
            time.sleep(0.2)
        children.append(subprocess.Popen([sys.executable,'-m','gunicorn','--bind','127.0.0.1:8081','--workers','1','--threads','1',
          '--timeout','180','--max-requests','500','--error-logfile','-','tools.production_runtime.wsgi:application']))
        children.append(subprocess.Popen(['/usr/local/bin/oauth2-proxy','--config',os.environ['WNC_OAUTH_PROXY_CONFIG'],
          '--http-address','0.0.0.0:'+os.environ.get('PORT','10000')]))
        while all(p.poll() is None for p in children):time.sleep(1)
        raise RuntimeError('production_component_stopped')
    finally:
        try:
            controls=c.controls();controls['lanes']={k:False for k in LANES};controls['lease_expires']=0
            if state_store.enabled(c):state_store.disable(c)
            else:atomic_json(c.controls_path,controls)
        except Exception:pass  # Invalid/unreadable controls already fail closed; still stop children.
        for p in children:
            if p.poll() is None:p.terminate()
        for p in children:
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill()
if __name__=='__main__':main()
