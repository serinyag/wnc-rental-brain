"""Dedicated production Asana OAuth; credentials never enter diagnostics."""
import base64
import hashlib
import json
import secrets
import ssl
import time
import urllib.parse
import urllib.request
import certifi
from .microsoft_provisioning import Keychain
from .network import open_provider

CLIENT_ID = '1219360164957582'
REDIRECT = 'urn:ietf:wg:oauth:2.0:oob'
SCOPES = ('projects:read', 'tasks:read', 'tasks:write')


def begin_authorization():
    verifier = secrets.token_urlsafe(48)
    state = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    store = Keychain(CLIENT_ID, service='WNC Rental Brain production Asana OAuth pending flow')
    value = json.dumps({'verifier': verifier, 'state': state, 'created_at': time.time()})
    if store.read() is None:
        store.add(value)
    else:
        store.replace(value)
    return 'https://app.asana.com/-/oauth_authorize?' + urllib.parse.urlencode({
        'client_id': CLIENT_ID, 'redirect_uri': REDIRECT, 'response_type': 'code',
        'state': state, 'code_challenge_method': 'S256', 'code_challenge': challenge,
        'scope': ' '.join(SCOPES)})


def request_token(fields):
    request = urllib.request.Request('https://app.asana.com/-/oauth_token',
        data=urllib.parse.urlencode(fields).encode(),
        headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    try:
        with open_provider(request, timeout=15, context=ssl.create_default_context(cafile=certifi.where())) as response:
            if response.status != 200:
                raise ValueError('asana_token_http_failure')
            payload = json.loads(response.read(65537))
    except Exception:
        raise ValueError('asana_token_exchange_failed_no_secret_details') from None
    return payload


def validate_token(payload):
    if (not isinstance(payload, dict) or not isinstance(payload.get('access_token'), str)
        or len(payload['access_token']) < 10 or payload.get('token_type', '').lower() != 'bearer'
        or type(payload.get('expires_in')) is not int or not 60 <= payload['expires_in'] <= 86400):
        raise ValueError('asana_token_response_invalid')
    if 'scope' in payload and set(payload['scope'].split()) != set(SCOPES):
        raise ValueError('asana_token_scope_mismatch')
    return payload


class RefreshingToken:
    """Cache a short-lived token; persist any refresh rotation before use."""
    def __init__(self, client_secret, refresh_token, *, persist_refresh, request=request_token, clock=time.time):
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.persist_refresh = persist_refresh
        self.request = request
        self.clock = clock
        self.access_token = None
        self.expires_at = 0

    def get(self):
        if self.access_token and self.clock() < self.expires_at - 60:
            return self.access_token
        payload = validate_token(self.request({'grant_type': 'refresh_token', 'client_id': CLIENT_ID,
            'client_secret': self.client_secret, 'refresh_token': self.refresh_token}))
        rotated = payload.get('refresh_token')
        if rotated:
            if not isinstance(rotated, str) or len(rotated) < 10:
                raise ValueError('asana_refresh_response_invalid')
            self.persist_refresh(rotated)
            self.refresh_token = rotated
        self.access_token = payload['access_token']
        self.expires_at = self.clock() + payload['expires_in']
        return self.access_token


def environment_token_provider():
    """Render secrets supply refresh credentials; unexpected rotation stops use.

    No refresh request occurs until the adapter asks for an authorization token.
    A rotated refresh token must be durably stored before provider work resumes.
    """
    import os
    secret=os.environ.get('PRODUCTION_ASANA_OAUTH_CLIENT_SECRET')
    refresh=os.environ.get('PRODUCTION_ASANA_OAUTH_REFRESH_TOKEN')
    if not secret or not refresh:
        raise ValueError('production_asana_oauth_credentials_missing')
    def persist(value):
        if value != refresh:
            raise ValueError('asana_refresh_rotation_requires_secure_persistence')
    return RefreshingToken(secret,refresh,persist_refresh=persist).get
