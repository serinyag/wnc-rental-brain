"""Verified, role-scoped database transport for shared-project production."""
from pathlib import Path
import psycopg
from .schema_isolation import qualify_runtime_sql

CA = Path(__file__).parent / 'certs/supabase-prod-ca-2021.crt'

class ProductionCursor(psycopg.Cursor):
    def execute(self, query, params=None, *, prepare=None, binary=None):
        if not isinstance(query, str):
            raise ValueError('production_query_must_be_explicit_sql')
        return super().execute(qualify_runtime_sql(query), params, prepare=prepare, binary=binary)

    def executemany(self, query, params_seq, *, returning=False):
        if not isinstance(query, str):
            raise ValueError('production_query_must_be_explicit_sql')
        return super().executemany(qualify_runtime_sql(query), params_seq, returning=returning)


def connect(dsn, *, contract=None, **kwargs):
    from .config import ProductionContract
    contract = contract or ProductionContract.from_env()
    contract.validate_database(dsn)
    if contract.manifest['database'].get('architecture') != 'shared_project_schemas_v1':
        return psycopg.connect(dsn, **kwargs)
    if any(k in kwargs for k in ('cursor_factory', 'sslmode', 'sslrootcert', 'user', 'password', 'host', 'dbname')):
        raise ValueError('production_connection_override_forbidden')
    return psycopg.connect(dsn, sslrootcert=str(CA), cursor_factory=ProductionCursor, **kwargs)
