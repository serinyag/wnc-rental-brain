import pytest
from .asana_oauth import RefreshingToken, SCOPES, validate_token


def token(**changes):
    return dict(access_token='fake-access-token', token_type='bearer', expires_in=3600,
                scope=' '.join(SCOPES), **changes)


def test_refresh_caches_and_persists_rotation_before_return():
    now=[1000]; calls=[]; stored=[]
    def request(fields):
        calls.append(fields)
        return token(refresh_token='rotated-fake-refresh')
    provider=RefreshingToken('fake-secret','initial-fake-refresh',
        persist_refresh=stored.append,request=request,clock=lambda:now[0])
    assert provider.get()=='fake-access-token' and stored==['rotated-fake-refresh']
    assert provider.get()=='fake-access-token' and len(calls)==1
    now[0]+=3550
    provider.get()
    assert len(calls)==2 and calls[1]['refresh_token']=='rotated-fake-refresh'


def test_failed_refresh_persistence_never_returns_or_caches_token():
    def refuse(_):raise OSError('storage unavailable')
    provider=RefreshingToken('fake-secret','fake-refresh',persist_refresh=refuse,
        request=lambda _:token(refresh_token='rotated-fake-refresh'))
    with pytest.raises(OSError):provider.get()
    assert provider.access_token is None


def test_broader_scopes_rejected():
    value=token();value['scope']+=' tasks:delete'
    with pytest.raises(ValueError):validate_token(value)
