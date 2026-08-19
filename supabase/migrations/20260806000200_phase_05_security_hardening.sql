alter table public.booking_fee_rules enable row level security;
alter table public.cancellation_rules enable row level security;
alter table public.capacity_rules enable row level security;
alter table public.catering_supplier_rules enable row level security;
alter table public.expedited_surcharge_rules enable row level security;
alter table public.facilitator_requirement_rules enable row level security;
alter table public.knowledge_audiences enable row level security;
alter table public.knowledge_categories enable row level security;
alter table public.knowledge_confidentiality_levels enable row level security;
alter table public.knowledge_document_corpus_states enable row level security;
alter table public.knowledge_document_version_audiences enable row level security;
alter table public.knowledge_document_version_rental_types enable row level security;
alter table public.knowledge_document_versions enable row level security;
alter table public.knowledge_documents enable row level security;
alter table public.logical_rules enable row level security;
alter table public.operational_requirements enable row level security;
alter table public.payment_rules enable row level security;
alter table public.rental_types enable row level security;
alter table public.rule_catalogue enable row level security;
alter table public.rule_source_links enable row level security;
alter table public.service_rules enable row level security;
alter table public.source_registry enable row level security;
alter table public.space_access_rules enable row level security;
alter table public.technical_capability_rules enable row level security;
alter table public.technical_equipment_inventory enable row level security;
alter table public.venue_spaces enable row level security;

revoke all on table
  public.booking_fee_rules,
  public.cancellation_rules,
  public.capacity_rules,
  public.catering_supplier_rules,
  public.expedited_surcharge_rules,
  public.facilitator_requirement_rules,
  public.knowledge_audiences,
  public.knowledge_categories,
  public.knowledge_confidentiality_levels,
  public.knowledge_document_corpus_states,
  public.knowledge_document_version_audiences,
  public.knowledge_document_version_rental_types,
  public.knowledge_document_versions,
  public.knowledge_documents,
  public.logical_rules,
  public.operational_requirements,
  public.payment_rules,
  public.rental_types,
  public.rule_catalogue,
  public.rule_source_links,
  public.service_rules,
  public.source_registry,
  public.space_access_rules,
  public.technical_capability_rules,
  public.technical_equipment_inventory,
  public.venue_spaces
from anon, authenticated, service_role;

revoke all on table
  public.current_booking_fee_rules,
  public.current_payment_rules,
  public.current_expedited_surcharge_rules,
  public.current_cancellation_rules,
  public.current_capacity_rules,
  public.current_space_access_rules,
  public.current_operational_requirements,
  public.current_catering_supplier_rules,
  public.current_technical_equipment_inventory,
  public.current_technical_capability_rules,
  public.current_service_rules,
  public.current_facilitator_requirement_rules
from anon, authenticated, service_role;

grant select on table
  public.current_booking_fee_rules,
  public.current_payment_rules,
  public.current_expedited_surcharge_rules,
  public.current_cancellation_rules,
  public.current_capacity_rules,
  public.current_space_access_rules,
  public.current_operational_requirements,
  public.current_catering_supplier_rules,
  public.current_technical_equipment_inventory,
  public.current_technical_capability_rules,
  public.current_service_rules,
  public.current_facilitator_requirement_rules
to anon, authenticated, service_role;

revoke execute on function api.get_booking_fee_rule(text, integer, date) from public, anon, authenticated;
revoke execute on function api.get_payment_rules(text, text, integer, date) from public, anon, authenticated;
revoke execute on function api.get_expedited_surcharge_rule(date, date, date) from public, anon, authenticated;
revoke execute on function api.get_cancellation_rules(text, date, date, text, date) from public, anon, authenticated;
revoke execute on function api.get_capacity_rule(text, text, text, date) from public, anon, authenticated;
revoke execute on function api.evaluate_capacity(text, text, text, integer, date) from public, anon, authenticated;
revoke execute on function api.get_space_access_rule(text, text, date) from public, anon, authenticated;
revoke execute on function api.evaluate_space_access(text, text, date) from public, anon, authenticated;
revoke execute on function api.get_operational_requirements(text, text, text, boolean, text, date) from public, anon, authenticated;
revoke execute on function api.get_catering_supplier_rules(text, text, text, text, boolean, date) from public, anon, authenticated;
revoke execute on function api.get_technical_equipment_inventory(text, text) from public, anon, authenticated;
revoke execute on function api.evaluate_technical_equipment_quantity(text, integer) from public, anon, authenticated;
revoke execute on function api.get_technical_capability(text, text, text, text, date) from public, anon, authenticated;
revoke execute on function api.evaluate_technical_requirement(text, date) from public, anon, authenticated;
revoke execute on function api.get_service_rules(text, text, date) from public, anon, authenticated;
revoke execute on function api.get_facilitator_requirements(text, date) from public, anon, authenticated;
