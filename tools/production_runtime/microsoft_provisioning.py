"""Bounded provisioning preflight; secrets use private pipes and macOS Keychain.

No workflow ingestion, mailbox mutation, raw token, or message metadata is saved.
Run explicitly by an authorized administrator, never as a runtime worker.
"""
import base64
import ctypes
import json
from pathlib import Path
import subprocess
import ssl
import certifi
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'docs/production_microsoft_provisioning'
SERVICE = b'WNC Rental Brain PRODUCTION Microsoft client secret'


class Keychain:
    def __init__(self, account, *, service=SERVICE):
        self.service = service if isinstance(service, bytes) else service.encode()
        self.account = account.encode()
        self.api = ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
        self.handle = ctypes.c_void_p()
        self.api.SecKeychainCopyDefault.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        self.api.SecKeychainGetStatus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        self.api.SecKeychainFindGenericPassword.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
        self.api.SecKeychainAddGenericPassword.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        self.api.SecKeychainItemFreeContent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        status = ctypes.c_uint32()
        if self.api.SecKeychainCopyDefault(ctypes.byref(self.handle)) or self.api.SecKeychainGetStatus(self.handle, ctypes.byref(status)) or not status.value & 1:
            raise RuntimeError('secure_keychain_unavailable')

    def read(self):
        size, data = ctypes.c_uint32(), ctypes.c_void_p()
        result = self.api.SecKeychainFindGenericPassword(self.handle, len(self.service), self.service, len(self.account), self.account, ctypes.byref(size), ctypes.byref(data), None)
        if result == -25300:
            return None
        if result:
            raise RuntimeError('secure_keychain_read_failed')
        try:
            return ctypes.string_at(data, size.value).decode()
        finally:
            self.api.SecKeychainItemFreeContent(None, data)

    def add(self, secret):
        raw = secret.encode()
        if self.api.SecKeychainAddGenericPassword(self.handle, len(self.service), self.service, len(self.account), self.account, len(raw), raw, None):
            raise RuntimeError('secure_keychain_storage_failed_do_not_retry_creation')
        if self.read() != secret:
            raise RuntimeError('secure_keychain_roundtrip_failed')

    def replace(self, secret):
        """Rotate an existing item without putting its value in command arguments."""
        item = ctypes.c_void_p()
        size, data = ctypes.c_uint32(), ctypes.c_void_p()
        result = self.api.SecKeychainFindGenericPassword(self.handle, len(self.service), self.service, len(self.account), self.account, ctypes.byref(size), ctypes.byref(data), ctypes.byref(item))
        if result: raise RuntimeError('secure_keychain_rotation_item_missing')
        self.api.SecKeychainItemFreeContent(None, data)
        self.api.SecKeychainItemModifyAttributesAndData.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p]
        raw = secret.encode()
        if self.api.SecKeychainItemModifyAttributesAndData(item, None, len(raw), raw):
            raise RuntimeError('secure_keychain_rotation_failed')
        if self.read() != secret: raise RuntimeError('secure_keychain_rotation_roundtrip_failed')


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(url, *, token=None, data=None):
    if urllib.parse.urlsplit(url).hostname not in {'graph.microsoft.com', 'login.microsoftonline.com'}:
        raise RuntimeError('unexpected_provider_host')
    headers = {'Prefer': 'IdType="ImmutableId"'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if data is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        opener = urllib.request.build_opener(NoRedirects(), urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
        with opener.open(req, timeout=30) as response:
            return response.status, json.loads(response.read(256000))
    except urllib.error.HTTPError as error:
        # Do not retain error body, request credentials, headers, or token.
        return error.code, {}


def run():
    identity = json.loads((DIRECTORY / 'identity.json').read_text())
    client, tenant = identity['client_id'], identity['tenant_id']
    assert client not in identity['staging_client_ids']
    keychain = Keychain(client)
    secret = keychain.read()
    metadata_path = DIRECTORY / 'credential_metadata.json'
    if secret is None:
        if metadata_path.exists():
            raise RuntimeError('credential_exists_but_secure_storage_missing_reconcile_before_retry')
        # Child stdout is a private captured pipe, not command/tool output.
        script = r'''
$ErrorActionPreference='Stop'
Import-Module Microsoft.Graph.Applications
Connect-MgGraph -TenantId '7c9d7d19-2b22-4da3-975a-1fba6f29c366' -Scopes Application.ReadWrite.All -ContextScope CurrentUser -NoWelcome
$ctx=Get-MgContext
if($ctx.Account -ine 'Serinya@whennaturecalls.nl'){throw 'administrator_mismatch'}
$i=Get-Content 'docs/production_microsoft_provisioning/identity.json' -Raw | ConvertFrom-Json
$app=Get-MgApplication -ApplicationId $i.application_object_id
if(@($app.PasswordCredentials).Count -ne 0){throw 'credential_already_exists'}
$c=Add-MgApplicationPassword -ApplicationId $i.application_object_id -PasswordCredential @{displayName='Production pilot — Keychain custody';endDateTime=[DateTime]::UtcNow.AddDays(90)}
$m=@{credential_id=$c.KeyId;expires_at=$c.EndDateTime;exists=$true;secure_storage_verified=$false;store='macOS default Keychain';service='WNC Rental Brain PRODUCTION Microsoft client secret';account=$i.client_id}
$m | ConvertTo-Json | Set-Content 'docs/production_microsoft_provisioning/credential_metadata.json'
@{secret=$c.SecretText} | ConvertTo-Json -Compress
'''
        result = subprocess.run(['pwsh', '-NoLogo', '-NoProfile', '-Command', script], cwd=ROOT, capture_output=True, timeout=110)
        if result.returncode:
            raise RuntimeError('credential_creation_failed_reconcile_before_retry')
        secret = json.loads(result.stdout)['secret']
        keychain.add(secret)
        metadata = json.loads(metadata_path.read_text())
        metadata['secure_storage_verified'] = True
        metadata_path.write_text(json.dumps(metadata, indent=2) + '\n')
    form = urllib.parse.urlencode({'client_id': client, 'client_secret': secret, 'grant_type': 'client_credentials', 'scope': 'https://graph.microsoft.com/.default'}).encode()
    status, auth = request(f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token', data=form)
    if status != 200 or not auth.get('access_token'):
        raise RuntimeError(f'production_token_failed_http_{status}')
    token = auth['access_token']
    claims = json.loads(base64.urlsafe_b64decode(token.split('.')[1] + '==='))
    # Transport is TLS to Microsoft's token endpoint. Claims are checked for
    # identity consistency; this decode alone is not signature validation.
    if claims.get('tid') != tenant or claims.get('appid', claims.get('azp')) != client or claims.get('aud') not in {'https://graph.microsoft.com', '00000003-0000-0000-c000-000000000000'}:
        raise RuntimeError('production_token_identity_mismatch')
    record = {'token_acquired': True, 'tenant_verified': True, 'production_client_verified': True, 'graph_audience_verified': True, 'immutable_id_preference': True, 'mailbox_mutations': 0, 'ingested_messages': 0, 'persisted_checkpoints': 0}
    def graph(mailbox, endpoint):
        mailbox = urllib.parse.quote(mailbox, safe='')
        return request(f'https://graph.microsoft.com/v1.0/users/{mailbox}/{endpoint}', token=token)
    # Negative first: stop immediately if the unauthorized mailbox is accessible.
    code, _ = graph('Serinya@whennaturecalls.nl', 'mailFolders/inbox?$select=id')
    record['negative_mailbox'] = 'Serinya@whennaturecalls.nl'
    record['negative_http_status'] = code
    (DIRECTORY / 'graph_preflight.json').write_text(json.dumps(record, indent=2) + '\n')
    if code == 200:
        raise RuntimeError('PRODUCTION_OUTLOOK_SCOPE_TOO_BROAD')
    if code != 403:
        raise RuntimeError(f'negative_access_test_inconclusive_http_{code}')
    code, folder = graph(identity['mailbox'], 'mailFolders/inbox?$select=id,displayName')
    record['positive_inbox_http_status'] = code
    if code != 200 or not isinstance(folder.get('id'), str):
        (DIRECTORY / 'graph_preflight.json').write_text(json.dumps(record, indent=2) + '\n')
        raise RuntimeError(f'positive_inbox_failed_http_{code}')
    code, messages = graph(identity['mailbox'], 'mailFolders/inbox/messages?$top=1&$select=id,conversationId,receivedDateTime,internetMessageId')
    record['bounded_messages_http_status'] = code
    record['bounded_response_shape_valid'] = code == 200 and isinstance(messages.get('value'), list) and all(all(isinstance(m.get(k), str) for k in ('id', 'conversationId', 'receivedDateTime', 'internetMessageId')) for m in messages.get('value', []))
    code, delta = graph(identity['mailbox'], 'mailFolders/inbox/messages/delta?$select=id,conversationId,receivedDateTime,internetMessageId&$top=1')
    record['delta_http_status'] = code
    record['delta_shape_valid'] = code == 200 and isinstance(delta.get('value'), list) and any(k in delta for k in ('@odata.nextLink', '@odata.deltaLink'))
    # Returned message IDs and delta links remain memory-only; do not follow them.
    rbac = json.loads((DIRECTORY / 'exchange_verification.json').read_text())
    record['outbound_authorization'] = 'Exchange scoped ReadWrite/Send verified; no draft mutation or send probe'
    assert all(str(x['InScope']).lower() == 'true' for x in rbac['positive'])
    assert all(str(x['InScope']).lower() == 'false' for x in rbac['negative'])
    record['passed'] = record['bounded_response_shape_valid'] and record['delta_shape_valid']
    if record['passed']:
        record['marker'] = 'PRODUCTION_OUTLOOK_IDENTITY_PROVISIONED_AND_SCOPED'
    (DIRECTORY / 'graph_preflight.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        # Only our predefined, content-free errors may leave this process.
        message = str(exc) if isinstance(exc, RuntimeError) else 'provisioning_failed_no_secret_details'
        raise SystemExit(message) from None
