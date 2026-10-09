"""Entra delegated access tokens + explicit revocable named operator registry."""
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID
import jwt
from .config import read_json

ROLES=frozenset({'OPERATOR','APPROVER','DECISION_AUTHORITY','ADMIN'})
CURRENT=ContextVar('wnc_operator',default=None)
@dataclass(frozen=True)
class Principal:
    tenant: str
    oid: str
    roles: frozenset
    @property
    def actor(self):return 'entra:'+self.tenant+':'+self.oid
    def require(self, role):
        if role not in self.roles:raise PermissionError('operator_capability_denied')

def actor():
    p=CURRENT.get()
    if p is None:raise PermissionError('named_operator_required')
    return p.actor

class EntraVerifier:
    def __init__(self,contract):
        self.contract=contract
        self.auth=contract.manifest['auth']
        self.issuer='https://login.microsoftonline.com/'+self.auth['tenant_id']+'/v2.0'
        self.keys=jwt.PyJWKClient('https://login.microsoftonline.com/'+self.auth['tenant_id']+'/discovery/v2.0/keys',timeout=5)
    def verify(self,token):
        if len(token)>16384 or jwt.get_unverified_header(token).get('alg')!='RS256':raise PermissionError('operator_token_invalid')
        key=self.keys.get_signing_key_from_jwt(token).key
        claims=jwt.decode(token,key,algorithms=['RS256'],audience=self.auth['audience'],issuer=self.issuer,
            options={'require':['exp','iat','nbf','iss','aud','tid','oid','scp','azp']},leeway=30)
        if (claims['tid']!=self.auth['tenant_id'] or claims.get('idtyp')=='app' or
            'access_as_user' not in claims['scp'].split() or claims['azp'] not in self.auth['authorized_client_ids']):
            raise PermissionError('delegated_operator_token_required')
        UUID(claims['oid'])
        registry=self.contract.operator_registry()
        if registry.get('deployment_id')!=self.contract.manifest['deployment_id']:raise PermissionError('operator_registry_scope_mismatch')
        entry=registry.get('operators',{}).get(claims['oid'],{})
        roles=frozenset(entry.get('roles',[])) & frozenset(claims.get('roles',[]))
        if entry.get('enabled') is not True or not entry.get('name') or not roles or not roles<=ROLES:
            raise PermissionError('operator_revoked_or_unassigned')
        return Principal(claims['tid'],claims['oid'],roles)
