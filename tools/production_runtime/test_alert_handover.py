from contextlib import contextmanager
import pytest
from tools.production_runtime.test_production import production
from tools.production_runtime import alerts,state_store


def test_competing_worker_does_not_fence_active_send(production,monkeypatch):
    c,_,_=production
    monkeypatch.setattr(state_store,'enabled',lambda _:True)
    @contextmanager
    def busy(_):yield False
    monkeypatch.setattr(state_store,'alert_dispatch_lock',busy)
    monkeypatch.setattr(state_store,'unresolved_alerts',lambda _:pytest.fail('active owner inspected'))
    assert alerts.dispatch(c,sender=object())==0


def test_abandoned_claim_stays_fenced_under_exclusive_owner(production,monkeypatch):
    c,_,_=production;disabled=[]
    monkeypatch.setattr(state_store,'enabled',lambda _:True)
    @contextmanager
    def owned(_):yield True
    monkeypatch.setattr(state_store,'alert_dispatch_lock',owned)
    monkeypatch.setattr(state_store,'unresolved_alerts',lambda _:1)
    monkeypatch.setattr(state_store,'disable',lambda _:disabled.append(True))
    with pytest.raises(ValueError,match='reconciliation_required'):alerts.dispatch(c,sender=object())
    assert disabled==[True]


def test_shutdown_records_inflight_receipt_and_leaves_next_pending(production,monkeypatch):
    c,_,_=production;stopped=[];receipts=[];claimed=[]
    monkeypatch.setattr(state_store,'enabled',lambda _:True)
    @contextmanager
    def owned(_):yield True
    monkeypatch.setattr(state_store,'alert_dispatch_lock',owned)
    monkeypatch.setattr(state_store,'unresolved_alerts',lambda _:0)
    monkeypatch.setattr(state_store,'pending_alerts',lambda *_:[('a',{}),('b',{})])
    monkeypatch.setattr(state_store,'claim_alert',lambda _,key:claimed.append(key) or True)
    monkeypatch.setattr(state_store,'alert_receipt',lambda _,key,status,receipt:receipts.append((key,status)))
    monkeypatch.setattr(state_store,'heartbeat',lambda *_:None)
    class Sender:
        def send(self,*_):stopped.append(True);return {'status':'provider_accepted'}
    assert alerts.dispatch(c,sender=Sender(),stop_requested=lambda:bool(stopped))==1
    assert claimed==['a'] and receipts==[('a','accepted')]
