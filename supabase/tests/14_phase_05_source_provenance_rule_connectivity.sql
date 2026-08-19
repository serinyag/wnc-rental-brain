begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(40);

select results_eq(
  $sql$
    select role_code
    from public.knowledge_source_object_roles
    order by sort_order, role_code
  $sql$,
  $sql$
    values
      ('authoritative_editable_source'::text),
      ('export'::text),
      ('attachment'::text),
      ('supporting_source'::text)
  $sql$,
  'approved source object role codes are seeded'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_object_roles (
      role_code,
      display_name,
      description
    )
    values (
      'export',
      'Duplicate Export',
      'duplicate role code should fail'
    );
  $sql$,
  '23505',
  null,
  'duplicate source object role codes are rejected'
);

select results_eq(
  $sql$
    select relationship_type_code, target_kind
    from public.knowledge_rule_relationship_types
    order by relationship_type_code
  $sql$,
  $sql$
    values
      ('explains'::text, 'logical_rule'::text),
      ('governed_by'::text, 'logical_rule'::text),
      ('historically_explains'::text, 'rule_version'::text),
      ('operational_context_for'::text, 'logical_rule'::text),
      ('specifically_reflects'::text, 'rule_version'::text),
      ('superseded_because_rule_changed'::text, 'rule_version'::text)
  $sql$,
  'approved relationship types are seeded with the expected target kinds'
);

select throws_ok(
  $sql$
    insert into public.knowledge_rule_relationship_types (
      relationship_type_code,
      target_kind,
      display_name,
      description
    )
    values (
      'invalid_target_kind',
      'unsupported_target',
      'Invalid Target',
      'invalid target kind should fail'
    );
  $sql$,
  '23514',
  null,
  'invalid rule relationship target kinds are rejected'
);

select throws_ok(
  $sql$
    insert into public.knowledge_rule_relationship_types (
      relationship_type_code,
      target_kind,
      display_name,
      description
    )
    values (
      'governed_by',
      'logical_rule',
      'Duplicate Governed By',
      'duplicate relationship code should fail'
    );
  $sql$,
  '23505',
  null,
  'duplicate rule relationship type codes are rejected'
);

select lives_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      repository_relative_path,
      original_filename
    )
    values (
      'repository_file',
      'tests/phase5/provenance/repository-source-valid.md',
      'repository-source-valid.md'
    );
  $sql$,
  'valid repository-file source objects are accepted'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      original_filename
    )
    values (
      'repository_file',
      'repository-source-missing-path.md'
    );
  $sql$,
  '23514',
  null,
  'repository-file source objects require a repository-relative path'
);

select lives_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      storage_bucket,
      storage_object_key,
      original_filename
    )
    values (
      'supabase_storage',
      'private-knowledge',
      'phase5/storage-source-valid.pdf',
      'storage-source-valid.pdf'
    );
  $sql$,
  'valid Supabase Storage source objects are accepted'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      storage_bucket,
      original_filename
    )
    values (
      'supabase_storage',
      'private-knowledge',
      'storage-source-missing-key.pdf'
    );
  $sql$,
  '23514',
  null,
  'Supabase Storage source objects require both bucket and object key'
);

select lives_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      external_uri,
      original_filename
    )
    values (
      'external_uri',
      'https://example.test/phase5/source-valid',
      'external-source-valid.html'
    );
  $sql$,
  'valid external-uri source objects are accepted'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      original_filename
    )
    values (
      'external_uri',
      'external-source-missing-uri.html'
    );
  $sql$,
  '23514',
  null,
  'external-uri source objects require an external URI'
);

select lives_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      original_filename
    )
    values (
      'manual_reference',
      'MANUAL-REF-VALID',
      'manual-reference-valid.txt'
    );
  $sql$,
  'valid manual-reference source objects are accepted'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      original_filename
    )
    values (
      'manual_reference',
      'manual-reference-missing-key.txt'
    );
  $sql$,
  '23514',
  null,
  'manual-reference source objects require a manual reference key'
);

select throws_ok(
  $sql$
    do $$
    begin
      insert into public.knowledge_source_objects (
        origin_type,
        repository_relative_path,
        original_filename
      )
      values (
        'repository_file',
        'tests/phase5/provenance/duplicate-repository-path.md',
        'duplicate-repository-path-a.md'
      );

      insert into public.knowledge_source_objects (
        origin_type,
        repository_relative_path,
        original_filename
      )
      values (
        'repository_file',
        'tests/phase5/provenance/duplicate-repository-path.md',
        'duplicate-repository-path-b.md'
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate repository-file locators are rejected'
);

select throws_ok(
  $sql$
    do $$
    begin
      insert into public.knowledge_source_objects (
        origin_type,
        storage_bucket,
        storage_object_key,
        original_filename
      )
      values (
        'supabase_storage',
        'private-knowledge',
        'phase5/duplicate-storage-key.pdf',
        'duplicate-storage-key-a.pdf'
      );

      insert into public.knowledge_source_objects (
        origin_type,
        storage_bucket,
        storage_object_key,
        original_filename
      )
      values (
        'supabase_storage',
        'private-knowledge',
        'phase5/duplicate-storage-key.pdf',
        'duplicate-storage-key-b.pdf'
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate Supabase Storage locators are rejected'
);

select lives_ok(
  $sql$
    do $$
    begin
      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        checksum_sha256,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-CHECKSUM-ONE',
        'same-checksum-across-two-objects',
        'checksum-object-one.txt'
      );

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        checksum_sha256,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-CHECKSUM-TWO',
        'same-checksum-across-two-objects',
        'checksum-object-two.txt'
      );
    end
    $$;
  $sql$,
  'identical checksums remain allowed across distinct source objects'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      file_size_bytes,
      original_filename
    )
    values (
      'manual_reference',
      'MANUAL-NEGATIVE-SIZE',
      -1,
      'negative-file-size.txt'
    );
  $sql$,
  '23514',
  null,
  'negative source-object file sizes are rejected'
);

select is(
  (
    select personal_information_status
    from public.knowledge_source_objects
    where manual_reference_key = 'MANUAL-REF-VALID'
  ),
  'unknown',
  'source-object personal-information status defaults to unknown'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      personal_information_status,
      original_filename
    )
    values (
      'manual_reference',
      'MANUAL-INVALID-PI-STATUS',
      'maybe',
      'invalid-pi-status.txt'
    );
  $sql$,
  '23514',
  null,
  'invalid personal-information status values are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      test_source_registry_id bigint;
    begin
      insert into public.source_registry (
        source_code,
        title,
        source_type,
        authority_level,
        lifecycle_status,
        original_filename,
        relative_source_path
      )
      values (
        'TEST_PHASE5_52C_SOURCE_REGISTRY_BRIDGE',
        'Phase 5.2C Source Registry Bridge Test',
        'test_source',
        'reference_only',
        'current',
        'phase5-52c-source-registry-bridge.txt',
        'tests/phase5/source-registry-bridge.txt'
      )
      returning id into test_source_registry_id;

      insert into public.knowledge_source_objects (
        source_registry_id,
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        test_source_registry_id,
        'manual_reference',
        'MANUAL-BRIDGED-SOURCE-OBJECT',
        'bridged-source-object.txt'
      );
    end
    $$;
  $sql$,
  'knowledge source objects can optionally bridge to valid source_registry rows'
);

select throws_ok(
  $sql$
    insert into public.knowledge_source_objects (
      source_registry_id,
      origin_type,
      manual_reference_key,
      original_filename
    )
    values (
      999999999,
      'manual_reference',
      'MANUAL-INVALID-SOURCE-REGISTRY',
      'invalid-source-registry-bridge.txt'
    );
  $sql$,
  '23503',
  null,
  'invalid source_registry bridges are rejected'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      source_object_id bigint;
      role_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into role_id
      from public.knowledge_source_object_roles
      where role_code = 'authoritative_editable_source';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_VALID_SOURCE_LINK_DOC',
        'Phase 5.2C Valid Source Link Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-VALID-SOURCE-LINK',
        'valid-source-link.txt'
      )
      returning id into source_object_id;

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition,
        is_preferred_extraction_source,
        is_primary_representation
      )
      values (
        version_id,
        source_object_id,
        role_id,
        'eligible_for_extraction',
        true,
        true
      );
    end
    $$;
  $sql$,
  'valid document-version source-object relationships are accepted'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      source_object_id bigint;
      role_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into role_id
      from public.knowledge_source_object_roles
      where role_code = 'supporting_source';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_DUP_SOURCE_LINK_DOC',
        'Phase 5.2C Duplicate Source Link Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-DUP-SOURCE-LINK',
        'duplicate-source-link.txt'
      )
      returning id into source_object_id;

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition
      )
      values (
        version_id,
        source_object_id,
        role_id,
        'supporting_only'
      );

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition
      )
      values (
        version_id,
        source_object_id,
        role_id,
        'supporting_only'
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate document-version source-object relationships are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      source_object_id bigint;
      role_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into role_id
      from public.knowledge_source_object_roles
      where role_code = 'supporting_source';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_INELIGIBLE_PREF_DOC',
        'Phase 5.2C Ineligible Preferred Source Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-INELIGIBLE-PREFERRED',
        'ineligible-preferred.txt'
      )
      returning id into source_object_id;

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition,
        is_preferred_extraction_source
      )
      values (
        version_id,
        source_object_id,
        role_id,
        'supporting_only',
        true
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'preferred extraction sources must be eligible for extraction'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      first_source_object_id bigint;
      second_source_object_id bigint;
      role_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into role_id
      from public.knowledge_source_object_roles
      where role_code = 'authoritative_editable_source';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_DOUBLE_PREFERRED_DOC',
        'Phase 5.2C Double Preferred Source Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-DOUBLE-PREFERRED-ONE',
        'double-preferred-one.txt'
      )
      returning id into first_source_object_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-DOUBLE-PREFERRED-TWO',
        'double-preferred-two.txt'
      )
      returning id into second_source_object_id;

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition,
        is_preferred_extraction_source
      )
      values (
        version_id,
        first_source_object_id,
        role_id,
        'eligible_for_extraction',
        true
      );

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition,
        is_preferred_extraction_source
      )
      values (
        version_id,
        second_source_object_id,
        role_id,
        'eligible_for_extraction',
        true
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'only one preferred extraction source is allowed per document version'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      first_source_object_id bigint;
      second_source_object_id bigint;
      role_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into role_id
      from public.knowledge_source_object_roles
      where role_code = 'export';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_DOUBLE_PRIMARY_DOC',
        'Phase 5.2C Double Primary Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-DOUBLE-PRIMARY-ONE',
        'double-primary-one.txt'
      )
      returning id into first_source_object_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-DOUBLE-PRIMARY-TWO',
        'double-primary-two.txt'
      )
      returning id into second_source_object_id;

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition,
        is_primary_representation
      )
      values (
        version_id,
        first_source_object_id,
        role_id,
        'supporting_only',
        true
      );

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition,
        is_primary_representation
      )
      values (
        version_id,
        second_source_object_id,
        role_id,
        'supporting_only',
        true
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'only one primary representation is allowed per document version'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      source_object_id bigint;
      role_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into role_id
      from public.knowledge_source_object_roles
      where role_code = 'supporting_source';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_EXCLUDED_HISTORICAL_DOC',
        'Phase 5.2C Excluded Historical Source Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_source_objects (
        origin_type,
        manual_reference_key,
        original_filename
      )
      values (
        'manual_reference',
        'MANUAL-EXCLUDED-HISTORICAL',
        'excluded-historical.txt'
      )
      returning id into source_object_id;

      insert into public.knowledge_document_version_source_objects (
        document_version_id,
        source_object_id,
        source_object_role_id,
        source_usage_disposition,
        representation_notes
      )
      values (
        version_id,
        source_object_id,
        role_id,
        'excluded_from_extraction',
        'historical source retained for provenance only'
      );
    end
    $$;
  $sql$,
  'excluded source representations can remain linked for historical provenance'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'governed_by';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_52C_LOGICAL_RELATIONSHIP_RULE',
        'testing'
      );

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_LOGICAL_RELATIONSHIP_DOC',
        'Phase 5.2C Logical Relationship Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_logical_rules (
        document_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        version_id,
        'TEST_PHASE5_52C_LOGICAL_RELATIONSHIP_RULE',
        relationship_type_id
      );
    end
    $$;
  $sql$,
  'valid document-version logical-rule relationships are accepted'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'governed_by';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_UNKNOWN_LOGICAL_RULE_DOC',
        'Phase 5.2C Unknown Logical Rule Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_logical_rules (
        document_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        version_id,
        'TEST_PHASE5_52C_UNKNOWN_LOGICAL_RULE',
        relationship_type_id
      );
    end
    $$;
  $sql$,
  '23503',
  null,
  'unknown logical rule codes are rejected from document-version logical-rule links'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'explains';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_52C_DUP_LOGICAL_RELATIONSHIP_RULE',
        'testing'
      );

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_DUP_LOGICAL_RELATIONSHIP_DOC',
        'Phase 5.2C Duplicate Logical Relationship Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_logical_rules (
        document_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        version_id,
        'TEST_PHASE5_52C_DUP_LOGICAL_RELATIONSHIP_RULE',
        relationship_type_id
      );

      insert into public.knowledge_document_version_logical_rules (
        document_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        version_id,
        'TEST_PHASE5_52C_DUP_LOGICAL_RELATIONSHIP_RULE',
        relationship_type_id
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate logical-rule relationships are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'specifically_reflects';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_52C_WRONG_LOGICAL_TARGET_RULE',
        'testing'
      );

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_WRONG_LOGICAL_TARGET_DOC',
        'Phase 5.2C Wrong Logical Target Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_logical_rules (
        document_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        version_id,
        'TEST_PHASE5_52C_WRONG_LOGICAL_TARGET_RULE',
        relationship_type_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'rule-version-only relationship types are rejected from logical-rule relationships'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      rule_version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'specifically_reflects';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_52C_RULE_VERSION_RELATIONSHIP_RULE',
        'testing'
      );

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_PHASE5_52C_RULE_VERSION_RELATIONSHIP_RULE',
        'testing',
        'hard_rule',
        1,
        'draft',
        'phase 5.2c exact rule-version relationship test'
      )
      returning id into rule_version_id;

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_RULE_VERSION_RELATIONSHIP_DOC',
        'Phase 5.2C Rule Version Relationship Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_rule_versions (
        document_version_id,
        rule_version_id,
        relationship_type_id
      )
      values (
        version_id,
        rule_version_id,
        relationship_type_id
      );
    end
    $$;
  $sql$,
  'valid document-version exact rule-version relationships are accepted'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'specifically_reflects';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_UNKNOWN_RULE_VERSION_DOC',
        'Phase 5.2C Unknown Rule Version Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_rule_versions (
        document_version_id,
        rule_version_id,
        relationship_type_id
      )
      values (
        version_id,
        999999999,
        relationship_type_id
      );
    end
    $$;
  $sql$,
  '23503',
  null,
  'unknown exact rule-version ids are rejected from document-version exact links'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      rule_version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'historically_explains';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_52C_DUP_RULE_VERSION_RELATIONSHIP_RULE',
        'testing'
      );

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_PHASE5_52C_DUP_RULE_VERSION_RELATIONSHIP_RULE',
        'testing',
        'hard_rule',
        1,
        'draft',
        'phase 5.2c duplicate exact rule-version relationship test'
      )
      returning id into rule_version_id;

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_DUP_RULE_VERSION_RELATIONSHIP_DOC',
        'Phase 5.2C Duplicate Rule Version Relationship Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_rule_versions (
        document_version_id,
        rule_version_id,
        relationship_type_id
      )
      values (
        version_id,
        rule_version_id,
        relationship_type_id
      );

      insert into public.knowledge_document_version_rule_versions (
        document_version_id,
        rule_version_id,
        relationship_type_id
      )
      values (
        version_id,
        rule_version_id,
        relationship_type_id
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate exact rule-version relationships are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      rule_version_id bigint;
      relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'governed_by';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_52C_WRONG_RULE_VERSION_TARGET_RULE',
        'testing'
      );

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_PHASE5_52C_WRONG_RULE_VERSION_TARGET_RULE',
        'testing',
        'hard_rule',
        1,
        'draft',
        'phase 5.2c wrong exact rule-version target test'
      )
      returning id into rule_version_id;

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_WRONG_RULE_VERSION_TARGET_DOC',
        'Phase 5.2C Wrong Rule Version Target Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_rule_versions (
        document_version_id,
        rule_version_id,
        relationship_type_id
      )
      values (
        version_id,
        rule_version_id,
        relationship_type_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'logical-rule-only relationship types are rejected from exact rule-version relationships'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_level_id bigint;
      document_id bigint;
      version_id bigint;
      rule_version_id bigint;
      logical_relationship_type_id bigint;
      exact_relationship_type_id bigint;
    begin
      select id
      into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id
      into confidentiality_level_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id
      into logical_relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'explains';

      select id
      into exact_relationship_type_id
      from public.knowledge_rule_relationship_types
      where relationship_type_code = 'specifically_reflects';

      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_52C_DUAL_SEMANTICS_RULE',
        'testing'
      );

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_PHASE5_52C_DUAL_SEMANTICS_RULE',
        'testing',
        'hard_rule',
        1,
        'draft',
        'phase 5.2c dual semantics test'
      )
      returning id into rule_version_id;

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'TEST_PHASE5_52C_DUAL_SEMANTICS_DOC',
        'Phase 5.2C Dual Semantics Document',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'reference_only',
        confidentiality_level_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_logical_rules (
        document_version_id,
        rule_code,
        relationship_type_id
      )
      values (
        version_id,
        'TEST_PHASE5_52C_DUAL_SEMANTICS_RULE',
        logical_relationship_type_id
      );

      insert into public.knowledge_document_version_rule_versions (
        document_version_id,
        rule_version_id,
        relationship_type_id
      )
      values (
        version_id,
        rule_version_id,
        exact_relationship_type_id
      );
    end
    $$;
  $sql$,
  'one document version can simultaneously link to a logical rule and an exact rule version'
);

select results_eq(
  $sql$
    select c.relname
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in (
        'knowledge_source_object_roles',
        'knowledge_rule_relationship_types',
        'knowledge_source_objects',
        'knowledge_document_version_source_objects',
        'knowledge_document_version_logical_rules',
        'knowledge_document_version_rule_versions'
      )
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('knowledge_document_version_logical_rules'::name),
      ('knowledge_document_version_rule_versions'::name),
      ('knowledge_document_version_source_objects'::name),
      ('knowledge_rule_relationship_types'::name),
      ('knowledge_source_object_roles'::name),
      ('knowledge_source_objects'::name)
  $sql$,
  'RLS is enabled on all new public provenance and connectivity tables'
);

select is(
  (
    select count(*)
    from pg_class c
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in (
        'knowledge_source_object_roles',
        'knowledge_rule_relationship_types',
        'knowledge_source_objects',
        'knowledge_document_version_source_objects',
        'knowledge_document_version_logical_rules',
        'knowledge_document_version_rule_versions'
      )
      and c.relforcerowsecurity
  ),
  0::bigint,
  'FORCE ROW LEVEL SECURITY is not enabled on the new tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in (
        'knowledge_source_object_roles',
        'knowledge_rule_relationship_types',
        'knowledge_source_objects',
        'knowledge_document_version_source_objects',
        'knowledge_document_version_logical_rules',
        'knowledge_document_version_rule_versions'
      )
      and rtg.grantee = 'PUBLIC'
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRIGGER', 'REFERENCES', 'TRUNCATE')
  ),
  0::bigint,
  'no PUBLIC table privileges remain on the new provenance and connectivity tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in (
        'knowledge_source_object_roles',
        'knowledge_rule_relationship_types',
        'knowledge_source_objects',
        'knowledge_document_version_source_objects',
        'knowledge_document_version_logical_rules',
        'knowledge_document_version_rule_versions'
      )
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRIGGER', 'REFERENCES', 'TRUNCATE')
  ),
  0::bigint,
  'no direct anon, authenticated, or service_role table privileges were introduced on the new tables'
);

select * from finish();
rollback;
