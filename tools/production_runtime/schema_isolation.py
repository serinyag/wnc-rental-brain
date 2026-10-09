"""Explicit namespace compilation for the approved shared-project architecture.

Migration compilation is only for trusted, hash-pinned repository SQL. Runtime
queries use a separate lexer that preserves literals and never interpolates data.
Database grants, not SQL rewriting alone, form the authorization boundary.
"""
import hashlib
import re

SCHEMAS = {'public': 'rental_production', 'private': 'rental_production_private', 'api': 'rental_production_api'}
ROLES = {'anon': 'wnc_production_reader', 'authenticated': 'wnc_production_operator', 'service_role': 'wnc_production_runtime', 'wnc_lifecycle_executor': 'wnc_production_lifecycle_executor'}


def compile_migration(source):
    """Transform trusted migration definitions, including function SQL bodies."""
    compiled = re.sub(r'\b(public|private|api)\.', lambda m: SCHEMAS[m[1]] + '.', source)
    compiled = re.sub(r"'(public|private|api)'", lambda m: "'" + SCHEMAS[m[1]] + "'", compiled)
    compiled = re.sub(r'\b(create\s+schema\s+(?:if\s+not\s+exists\s+)?)(public|private|api)\b', lambda m: m[1] + SCHEMAS[m[2]], compiled, flags=re.I)
    compiled = re.sub(r'\b(search_path\s*=\s*)([a-z_, ]+)', lambda m: m[1] + re.sub(r'\b(public|private|api)\b', lambda x: SCHEMAS[x[1]], m[2]), compiled, flags=re.I)
    compiled = re.sub(r'\b(schema\s+)(public|private|api)(\s*[,;]|\s+)', lambda m: m[1] + SCHEMAS[m[2]] + m[3], compiled, flags=re.I)
    # Schema privilege lists can contain multiple schemas after the first.
    compiled = re.sub(r'\b(schema\s+)([a-z_, ]+?)(\s+(?:to|from)\b)', lambda m: m[1] + re.sub(r'\b(public|private|api)\b', lambda x: SCHEMAS[x[1]], m[2]) + m[3], compiled, flags=re.I)
    for old, new in ROLES.items():
        compiled = re.sub(r'\b' + old + r'\b', new, compiled)
    # Provisioning owns the one outer transaction.
    return re.sub(r'^\s*(?:begin|commit)\s*;\s*$', '', compiled, flags=re.I|re.M)


def migration_receipt(filename, source):
    compiled = compile_migration(source)
    return {'file': filename, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'compiled_sha256': hashlib.sha256(compiled.encode()).hexdigest()}, compiled


def qualify_runtime_sql(sql):
    """Map qualified identifiers without modifying quoted values/comments.

    Dollar-quoted procedural SQL is intentionally refused: migrations are compiled
    separately; runtime code must invoke the installed governed functions.
    """
    tokens = re.compile(r"--[^\n]*(?:\n|$)|/\*.*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|\$[A-Za-z_0-9]*\$|\b[A-Za-z_][A-Za-z_0-9]*\b|.", re.S)
    pieces = list(tokens.finditer(sql))
    out = []
    for i, token in enumerate(pieces):
        value = token[0]
        if re.fullmatch(r'\$[A-Za-z_0-9]*\$', value):
            raise ValueError('production_runtime_procedural_sql_refused')
        identifier = value[1:-1] if value.startswith('"') else value
        if identifier in SCHEMAS:
            following = next((p[0] for p in pieces[i+1:] if not p[0].isspace()), None)
            if following == '.':
                value = SCHEMAS[identifier]
        out.append(value)
    return ''.join(out)
