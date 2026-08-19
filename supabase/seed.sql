-- Phase 4 seed strategy:
-- 1. seed source metadata that is stable and non-secret
-- 2. seed clearly approved canonical entities from the Data Dictionary
-- 3. seed only business-rule rows for domains that have passed architecture review

insert into public.source_registry (
  source_code,
  title,
  source_type,
  authority_level,
  lifecycle_status,
  original_filename,
  relative_source_path,
  effective_date,
  notes
)
values
  ('GOV-001', 'WNC Rental Knowledge Inventory', 'governance_workbook', 'authoritative', 'current', 'WNC Rental Knowledge Inventory.xlsm', 'Knowledge Governance/WNC Rental Knowledge Inventory.xlsm', '2026-07-31', 'Authority map and source precedence register.'),
  ('GOV-002', 'WNC Rental Policy Decisions & Change Log', 'governance_workbook', 'authoritative', 'current_controlled_record', 'WNC Rental Policy Decisions & Change Log.xlsm', 'Knowledge Governance/WNC Rental Policy Decisions & Change Log.xlsm', '2026-07-31', 'Canonical decision log with open-decision tracking.'),
  ('GOV-003', 'WNC Rental Data Dictionary', 'governance_workbook', 'authoritative', 'current_controlled_draft', 'WNC Rental Data Dictionary.xlsm', 'Knowledge Governance/WNC Rental Data Dictionary.xlsm', '2026-07-31', 'Canonical machine values and approved terminology.'),
  ('GOV-004', 'WNC Rental Informal Rules', 'governance_workbook', 'unverified', 'working_non_authoritative', 'WNC Rental Informal Rules.xlsm', 'Venue & Operations/WNC Rental Informal Rules.xlsm', '2026-07-31', 'Working guidance only; not safe for deterministic rule activation.'),
  ('CF-002', 'Updated Rental Lookbook 2026 export', 'lookbook_export', 'authoritative', 'current_export', 'Updated Rental Lookbook 2026.png', 'Client Facing Docs/Updated Rental Lookbook 2026.png', '2026-07-31', 'Supplied local artifact is a PNG export, not a PDF.'),
  ('CF-003', 'Studio Rental Terms editable master', 'terms_editable_master', 'authoritative', 'current', 'Studio Space _ Terms and Conditions.docx', 'Client Facing Docs/Studio Space _ Terms and Conditions.docx', '2026-07-31', 'Editable master controls the export.'),
  ('CF-004', 'Studio Rental Terms export', 'terms_export', 'authoritative', 'current_export', 'Studio Space _ Terms and Conditions (2).pdf', 'Client Facing Docs/Studio Space _ Terms and Conditions (2).pdf', '2026-07-31', 'Export appears older than editable master.'),
  ('CF-005', 'Full Venue Rental Terms editable master', 'terms_editable_master', 'authoritative', 'current', 'Full Venue _ Rental Terms and Conditions.docx', 'Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx', '2026-07-31', 'Editable master controls the export.'),
  ('CF-006', 'Full Venue Rental Terms export', 'terms_export', 'authoritative', 'current_export', 'Full Venue _ Rental Terms and Conditions.pdf', 'Client Facing Docs/Full Venue _ Rental Terms and Conditions.pdf', '2026-07-31', 'Export appears older than editable master.'),
  ('CF-007', 'WNC Rental Agreement Template', 'agreement_template', 'authoritative', 'current', 'WNC Rental Agreement Template.docx', 'Client Facing Docs/WNC Rental Agreement Template.docx', '2026-07-31', 'Controlled universal agreement template.'),
  ('COM-001-XLSM', 'WNC Rental Pricing, Fees & Payment Rules (xlsm)', 'commercial_workbook', 'authoritative', 'current_conflict_flagged', 'WNC Rental Pricing, Fees & Payment Rules.xlsm', 'Commercial Rules/WNC Rental Pricing, Fees & Payment Rules.xlsm', '2026-07-31', 'Conflicts with supplied xlsx variant and requires review.'),
  ('COM-001-XLSX', 'WNC Rental Pricing, Fees & Payment Rules (xlsx)', 'commercial_workbook', 'authoritative', 'current_conflict_flagged', 'WNC Rental Pricing, Fees & Payment Rules.xlsx', 'Venue & Operations/WNC Rental Pricing, Fees & Payment Rules.xlsx', '2026-07-31', 'Closer to the decision log on several fields, but relationship to master is unresolved.'),
  ('OPS-001', 'WNC Venue Rental Operations Manual', 'operations_manual', 'authoritative', 'current_controlled_draft', 'WNC Venue Rental Operations Manual.docx', 'Venue & Operations/WNC Venue Rental Operations Manual.docx', '2026-07-31', 'Operational rules and source precedence.'),
  ('OPS-002', 'WNC Venue Technical & Equipment Inventory', 'technical_inventory', 'authoritative', 'current', 'WNC Venue Technical & Equipment Inventory.xlsm', 'Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm', '2026-07-31', 'Includes spaces, capabilities, and capacity rules.'),
  ('SERV-001', 'WNC Rental Services Catalogue', 'catalogue_workbook', 'authoritative', 'current', 'WNC Rental Services Catalogue.xlsm', 'Catalogues/WNC Rental Services Catalogue.xlsm', '2026-07-31', 'Service-level and service-type definitions.'),
  ('SERV-003', 'WNC Catering, Beverage & Supplier Catalogue', 'catalogue_workbook', 'authoritative', 'current', 'WNC Catering, Beverage & Supplier Catalogue.xlsm', 'Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm', '2026-07-31', 'Supplier, catering, beverage, and external supplier requirements.'),
  ('TPL-001', 'Studio Rental Proposal Template', 'proposal_template', 'guidance', 'current', 'Studio Rental Proposal Template.docx', 'Checklists + Templates/Proposal Templates/Studio Rental Proposal Template.docx', '2026-07-31', 'Guidance only.'),
  ('TPL-002', 'Entire Venue Proposal Template', 'proposal_template', 'guidance', 'current', 'Entire Venue Proposal Template.docx', 'Checklists + Templates/Proposal Templates/Entire Venue Proposal Template.docx', '2026-07-31', 'Guidance only.'),
  ('TPL-003', 'Custom Scope Proposal Template', 'proposal_template', 'guidance', 'current', 'Custom Scope Proposal Template.docx', 'Checklists + Templates/Proposal Templates/Custom Scope Proposal Template.docx', '2026-07-31', 'Guidance only.'),
  ('TPL-004', 'Production Coordination Proposal Template', 'proposal_template', 'guidance', 'current', 'Production Coordination Proposal Template.docx', 'Checklists + Templates/Proposal Templates/Production Coordination Proposal Template.docx', '2026-07-31', 'Guidance only.'),
  ('TPL-005', 'Full Production Proposal Template', 'proposal_template', 'guidance', 'current', 'Full Production Proposal Template.docx', 'Checklists + Templates/Proposal Templates/Full Production Proposal Template.docx', '2026-07-31', 'Guidance only.'),
  ('TPL-006', 'WNC Rental Email Template Library', 'communication_template', 'guidance', 'current', 'WNC Rental Email Template Library.docx', 'Checklists + Templates/WNC Rental Email Template Library.docx', '2026-07-31', 'Communication guidance only.'),
  ('TPL-007', 'Discovery Call and Site Visit Checklist', 'checklist', 'guidance', 'current', 'WNC Rental Discovery Call & Site Visit Checklist.docx', 'Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx', '2026-07-31', 'Guidance and intake-fact source.'),
  ('TPL-009', 'Event Handover and Final Readiness Checklist', 'checklist', 'guidance', 'current', 'WNC Rental Event Handover & Final Readiness Checklist.docx', 'Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx', '2026-07-31', 'Guidance and final-info source.'),
  ('TPL-013', 'Rental Close-Out Checklist', 'checklist', 'guidance', 'current', 'WNC Rental Close-Out Checklist.docx', 'Checklists + Templates/WNC Rental Close-Out Checklist.docx', '2026-07-31', 'Guidance and close-out source.'),
  ('HC-AMO-000', 'WNC Rental Historical Case Library', 'historical_reference', 'reference_only', 'historical_reference', 'WNC Rental Historical Case Library.docx', 'Historical Cases/WNC Rental Historical Case Library.docx', '2026-07-31', 'Explicitly excluded from authoritative rule activation.')
on conflict (source_code) do update
set
  title = excluded.title,
  source_type = excluded.source_type,
  authority_level = excluded.authority_level,
  lifecycle_status = excluded.lifecycle_status,
  original_filename = excluded.original_filename,
  relative_source_path = excluded.relative_source_path,
  effective_date = excluded.effective_date,
  notes = excluded.notes;

insert into public.rental_types (
  rental_type_code,
  display_name,
  description
)
values
  ('studio_space', 'Studio Space', 'Rental of the Studio Space under the standard studio-rental scope.'),
  ('entire_venue', 'Entire Venue', 'Exclusive rental of the WNC venue for the agreed period, subject to final scope and access conditions.'),
  ('custom_scope', 'Custom Scope', 'A rental not fully covered by the standard Studio Space or Entire Venue products and therefore requiring a manual scope and quote.')
on conflict (rental_type_code) do update
set
  display_name = excluded.display_name,
  description = excluded.description;

insert into public.venue_spaces (
  space_code,
  display_name,
  description,
  sort_order
)
values
  ('studio_space', 'Studio Space', 'The main studio used for movement, wellness sessions, seated events, and standing events.', 1),
  ('one_to_one_room', '1:1 / Podcast Room', 'The single physical room used for 1:1 sessions and podcast or recording purposes.', 2),
  ('retail_area', 'Retail Area', 'The retail and bar area at the front of the venue.', 3),
  ('conversation_pit', 'Conversation Pit', 'The sunken conversation and seating area within the venue.', 4),
  ('storage_room', 'Storage Room', 'The room used for storage, including agreed furniture storage during venue clearing.', 5),
  ('back_office', 'Back Office', 'The internal staff and administration area.', 6),
  ('hallway_bathrooms', 'Hallway and Bathrooms', 'The circulation and bathroom areas included in the venue layout.', 7),
  ('other_space', 'Other Space', 'A non-standard or temporary space reference that requires a written description.', 8)
on conflict (space_code) do update
set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.knowledge_categories (
  category_code,
  display_name,
  description,
  sort_order
)
values
  ('governance_canonical', 'Governance Canonical', 'Canonical governance artifacts and structured policy knowledge owned as authoritative organizational truth.', 1),
  ('client_facing_controlled_document', 'Client-Facing Controlled Document', 'Controlled client-facing documents such as agreements, terms, and approved external materials.', 2),
  ('operational_procedure', 'Operational Procedure', 'Internal operating procedures, readiness checklists, and execution guidance for rentals.', 3),
  ('technical_venue_reference', 'Technical Venue Reference', 'Technical venue reference material such as inventory, capabilities, and space-support guidance.', 4),
  ('service_supplier_guidance', 'Service Supplier Guidance', 'Service, supplier, facilitator, catering, and support guidance used to plan rentals.', 5),
  ('proposal_guidance', 'Proposal Guidance', 'Proposal and quoting guidance used to scope or present rental offerings.', 6),
  ('communication_guidance', 'Communication Guidance', 'Communication templates and response-pattern guidance for rental conversations.', 7)
on conflict (category_code) do update
set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.knowledge_audiences (
  audience_code,
  display_name,
  description,
  sort_order
)
values
  ('knowledge_owner', 'Knowledge Owner', 'Internal owner responsible for maintaining and governing the knowledge artifact.', 1),
  ('rental_coordinator', 'Rental Coordinator', 'Team member coordinating rental scoping, proposal, and follow-up work.', 2),
  ('general_manager', 'General Manager', 'Leadership audience reviewing operational, commercial, or governance implications.', 3),
  ('operations', 'Operations', 'Operational team responsible for delivery, readiness, and venue execution details.', 4),
  ('facilities', 'Facilities', 'Facilities-oriented audience concerned with venue systems, condition, and building logistics.', 5),
  ('event_lead', 'Event Lead', 'Delivery lead responsible for event-specific execution and coordination.', 6),
  ('finance', 'Finance', 'Finance audience responsible for pricing, invoicing, and payment interpretation.', 7),
  ('marketing_brand', 'Marketing / Brand', 'Audience concerned with outward-facing presentation, language, and brand alignment.', 8),
  ('client_facing_staff', 'Client-Facing Staff', 'Staff who speak with clients and need controlled outward-facing knowledge guidance.', 9),
  ('prospective_client', 'Prospective Client', 'Potential client audience for approved external knowledge materials.', 10),
  ('confirmed_client', 'Confirmed Client', 'Confirmed client audience for approved external or delivery-stage materials.', 11),
  ('supplier_coordinator', 'Supplier Coordinator', 'Audience coordinating external suppliers, partners, and operational support providers.', 12)
on conflict (audience_code) do update
set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.knowledge_confidentiality_levels (
  level_code,
  display_name,
  description,
  sort_order
)
values
  ('externally_shareable', 'Externally Shareable', 'Content approved to be shared externally when the business context calls for it.', 1),
  ('internal', 'Internal', 'Internal organizational knowledge not intended for general external circulation.', 2),
  ('commercially_sensitive', 'Commercially Sensitive', 'Commercially sensitive material whose access should remain limited to appropriate internal roles.', 3),
  ('restricted', 'Restricted', 'Restricted knowledge requiring especially narrow internal handling and review before access.', 4)
on conflict (level_code) do update
set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.logical_rules (
  rule_code,
  rule_domain
)
values
  ('ACCESS_ENTIRE_VENUE_BACK_OFFICE_RESTRICTED', 'space_access'),
  ('ACCESS_ENTIRE_VENUE_CONVERSATION_PIT_INCLUDED', 'space_access'),
  ('ACCESS_ENTIRE_VENUE_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'space_access'),
  ('ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'space_access'),
  ('ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'space_access'),
  ('ACCESS_ENTIRE_VENUE_STORAGE_ROOM_RESTRICTED', 'space_access'),
  ('ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED', 'space_access'),
  ('ACCESS_STUDIO_BACK_OFFICE_RESTRICTED', 'space_access'),
  ('ACCESS_STUDIO_CONVERSATION_PIT_SHARED', 'space_access'),
  ('ACCESS_STUDIO_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'space_access'),
  ('ACCESS_STUDIO_ONE_TO_ONE_INCLUDED', 'space_access'),
  ('ACCESS_STUDIO_RETAIL_SHARED', 'space_access'),
  ('ACCESS_STUDIO_SPACE_INCLUDED', 'space_access'),
  ('ACCESS_STUDIO_STORAGE_ROOM_RESTRICTED', 'space_access'),
  ('CANCELLATION_CLIENT_30_OR_FEWER_RENTAL_PAYMENTS', 'cancellation'),
  ('CANCELLATION_CLIENT_30_OR_FEWER_THIRD_PARTY_COMMITTED_COSTS', 'cancellation'),
  ('CANCELLATION_CLIENT_BOOKING_FEE_NON_REFUNDABLE', 'cancellation'),
  ('CANCELLATION_CLIENT_BREACH_RETAIN_ALL_PAYMENTS', 'cancellation'),
  ('CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS', 'cancellation'),
  ('CANCELLATION_CLIENT_OVER_30_THIRD_PARTY_COMMITTED_COSTS', 'cancellation'),
  ('CANCELLATION_CLIENT_PRODUCTION_AND_COORDINATION_FEES_NON_REFUNDABLE', 'cancellation'),
  ('CANCELLATION_CLIENT_SECURITY_DEPOSIT_RETURNED_UNLESS_DEDUCTIONS', 'cancellation'),
  ('CANCELLATION_WNC_REFUND_ALL_FEES_AND_DEPOSITS', 'cancellation'),
  ('CAPACITY_BACK_OFFICE_NOT_EVENT_SPACE', 'capacity'),
  ('CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'capacity'),
  ('CAPACITY_HALLWAY_BATHROOMS_NOT_EVENT_SPACE', 'capacity'),
  ('CAPACITY_ONE_TO_ONE_REQUIRES_CONFIRMATION', 'capacity'),
  ('CAPACITY_RETAIL_STANDING', 'capacity'),
  ('CAPACITY_STORAGE_ROOM_NOT_EVENT_SPACE', 'capacity'),
  ('CAPACITY_STUDIO_LYING_DOWN', 'capacity'),
  ('CAPACITY_STUDIO_MOVEMENT', 'capacity'),
  ('CAPACITY_STUDIO_SEATED', 'capacity'),
  ('CAPACITY_STUDIO_STANDING', 'capacity'),
  ('CATER_BEVERAGE_PACKAGE_ALLOWED', 'catering_supplier'),
  ('CATER_COFFEE_MACHINE_AGREED_USE', 'catering_supplier'),
  ('CATER_EXTERNAL_BARISTA_ALLOWED', 'catering_supplier'),
  ('CATER_EXTERNAL_BARISTA_POWER_CONFIRM', 'catering_supplier'),
  ('CATER_EXTERNAL_BARISTA_STORAGE_CONFIRM', 'catering_supplier'),
  ('CATER_EXTERNAL_CATERER_ALLOWED', 'catering_supplier'),
  ('CATER_EXTERNAL_CATERER_POWER_CONFIRM', 'catering_supplier'),
  ('CATER_EXTERNAL_CATERER_STORAGE_CONFIRM', 'catering_supplier'),
  ('CATER_KITCHEN_LARGE_SCALE_PRODUCTION_CONFIRM', 'catering_supplier'),
  ('CATER_KITCHEN_READY_MADE_SUPPORT', 'catering_supplier'),
  ('CATER_SPARKLING_WATER_OPTIONAL', 'catering_supplier'),
  ('CATER_TAP_WATER_INCLUDED', 'catering_supplier'),
  ('CATER_VAT_COORDINATION_SERVICE_21_PERCENT', 'catering_supplier'),
  ('CATER_VAT_MIXED_SPLIT_REQUIRED', 'catering_supplier'),
  ('CATER_VAT_PRODUCTS_9_PERCENT', 'catering_supplier'),
  ('CATER_WNC_PARTNER_AVAILABLE', 'catering_supplier'),
  ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'expedited_surcharge'),
  ('FACILITATOR_CLIENT_PROVIDED_ALLOWED', 'service_facilitator'),
  ('FACILITATOR_CUSTOM_EXPERIENCE_DESIGN_MANUAL_REVIEW', 'service_facilitator'),
  ('FACILITATOR_NONE_NOT_APPLICABLE', 'service_facilitator'),
  ('FACILITATOR_RECOMMENDATION_REQUESTED_CONFIRMATION_REQUIRED', 'service_facilitator'),
  ('FACILITATOR_UNDER_CONSIDERATION_CONFIRMATION_REQUIRED', 'service_facilitator'),
  ('FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED', 'service_facilitator'),
  ('FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED', 'service_facilitator'),
  ('FEE_ENTIRE_VENUE_1_TO_3_HOUR_BOOKING', 'booking_fee'),
  ('FEE_ENTIRE_VENUE_4_TO_7_HOUR_BOOKING', 'booking_fee'),
  ('FEE_ENTIRE_VENUE_FULL_DAY_BOOKING', 'booking_fee'),
  ('FEE_STUDIO_1_TO_3_HOUR_BOOKING', 'booking_fee'),
  ('FEE_STUDIO_4_TO_8_HOUR_BOOKING', 'booking_fee'),
  ('OPER_BACK_OFFICE_PREPARATION_REQUIRED', 'operational_requirement'),
  ('OPER_CLEANING_RESET_CLIENT_RESPONSIBILITY', 'operational_requirement'),
  ('OPER_DELIVERIES_WITHIN_RENTAL_WINDOW', 'operational_requirement'),
  ('OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL', 'operational_requirement'),
  ('OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE', 'operational_requirement'),
  ('OPER_ENTIRE_VENUE_GRACE_PERIOD', 'operational_requirement'),
  ('OPER_ENTIRE_VENUE_MULTI_DAY_RESET_CLIENT_RESPONSIBILITY', 'operational_requirement'),
  ('OPER_INSTALLATION_EXTERIOR_ITEMS_CONDITIONAL', 'operational_requirement'),
  ('OPER_INSTALLATION_PLASTER_WALL_FIXINGS_PROHIBITED', 'operational_requirement'),
  ('OPER_INSTALLATION_REMOVABLE_ADHESIVES_CONDITIONAL', 'operational_requirement'),
  ('OPER_INSTALLATION_STRONG_BOND_ADHESIVES_PROHIBITED', 'operational_requirement'),
  ('OPER_INSTALLATION_WOODEN_BEAM_FIXINGS_CONDITIONAL', 'operational_requirement'),
  ('OPER_MULTI_DAY_TIMELINE_REQUIRED', 'operational_requirement'),
  ('OPER_OFF_TIMELINE_VISITS_BY_APPOINTMENT', 'operational_requirement'),
  ('OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', 'operational_requirement'),
  ('OPER_SETUP_START_AT_BOOKED_TIME', 'operational_requirement'),
  ('OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL', 'operational_requirement'),
  ('OPER_STUDIO_GRACE_PERIOD', 'operational_requirement'),
  ('OPER_SUPPLIERS_CLIENT_RESPONSIBILITY', 'operational_requirement'),
  ('OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY', 'operational_requirement'),
  ('OPER_SUPPLIER_INFORMATION_REQUIRED', 'operational_requirement'),
  ('OPER_WASTE_REMOVAL_CLIENT_RESPONSIBILITY', 'operational_requirement'),
  ('PAYMENT_CONFIRMATION_DEADLINE_0_TO_14_DAYS_100_PERCENT', 'payment'),
  ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_100_PERCENT', 'payment'),
  ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_30_PERCENT', 'payment'),
  ('PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT', 'payment'),
  ('PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS', 'payment'),
  ('PAYMENT_UPFRONT_100_PERCENT_OPTION', 'payment'),
  ('PAYMENT_UPFRONT_30_PERCENT_OPTION', 'payment'),
  ('SERVICE_ITEM_BEVERAGE_PACKAGE', 'service_facilitator'),
  ('SERVICE_ITEM_BREAKDOWN_RESET_SUPPORT', 'service_facilitator'),
  ('SERVICE_ITEM_CATERING_COORDINATION', 'service_facilitator'),
  ('SERVICE_ITEM_CLEANING_SERVICE', 'service_facilitator'),
  ('SERVICE_ITEM_EVENT_MANAGER', 'service_facilitator'),
  ('SERVICE_ITEM_EXPERIENCE_DESIGN', 'service_facilitator'),
  ('SERVICE_ITEM_FACILITATOR_SOURCING', 'service_facilitator'),
  ('SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING', 'service_facilitator'),
  ('SERVICE_ITEM_ONSITE_HOST', 'service_facilitator'),
  ('SERVICE_ITEM_OTHER_SERVICE', 'service_facilitator'),
  ('SERVICE_ITEM_PRODUCTION_COORDINATION', 'service_facilitator'),
  ('SERVICE_ITEM_SETUP_SUPPORT', 'service_facilitator'),
  ('SERVICE_ITEM_TECHNICAL_COORDINATION', 'service_facilitator'),
  ('SERVICE_LEVEL_FULL_PRODUCTION', 'service_facilitator'),
  ('SERVICE_LEVEL_SUPPORTED_RENTAL', 'service_facilitator'),
  ('SERVICE_LEVEL_VENUE_ONLY', 'service_facilitator'),
  ('TECH_ADDITIONAL_SOUND_SYSTEM_EXTERNAL', 'technical_capability'),
  ('TECH_BASIC_PROJECTOR_REQUEST_ONLY', 'technical_capability'),
  ('TECH_CASAMBI_LIGHTING_STANDARD', 'technical_capability'),
  ('TECH_DJ_SETUP_EXTERNAL', 'technical_capability'),
  ('TECH_EXTENSION_CABLE_REQUEST_ONLY', 'technical_capability'),
  ('TECH_FILMING_SETUP_NOT_AVAILABLE', 'technical_capability'),
  ('TECH_LIVESTREAM_SYSTEM_NOT_AVAILABLE', 'technical_capability'),
  ('TECH_MICROPHONES_EXTERNAL', 'technical_capability'),
  ('TECH_PLUG_POINTS_STANDARD', 'technical_capability'),
  ('TECH_POWER_GROUPS_STANDARD', 'technical_capability'),
  ('TECH_PRODUCTION_LIGHTING_EXTERNAL', 'technical_capability'),
  ('TECH_PROJECTION_SCREEN_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_AMPLIFIED_SOUND_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_BASIC_PROJECTION_CONFIRM', 'technical_capability'),
  ('TECH_REQ_CUSTOM_TECH_CONFIRM', 'technical_capability'),
  ('TECH_REQ_DJ_AUDIO_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_FILMING_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_HIGH_LOAD_POWER_CONFIRM', 'technical_capability'),
  ('TECH_REQ_LIVESTREAM_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_MICROPHONE_USE_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_ORDINARY_AUDIO_SUPPORTED', 'technical_capability'),
  ('TECH_REQ_PRODUCTION_LIGHTING_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_PROJECTION_WITH_SCREEN_EXTERNAL', 'technical_capability'),
  ('TECH_REQ_STANDARD_LIGHTING_SUPPORTED', 'technical_capability'),
  ('TECH_REQ_STANDARD_POWER_SUPPORTED', 'technical_capability'),
  ('TECH_REQ_STANDARD_WIFI_SUPPORTED', 'technical_capability'),
  ('TECH_SONOS_STANDARD', 'technical_capability'),
  ('TECH_VOLTAGE_STANDARD', 'technical_capability'),
  ('TECH_WIFI_STANDARD', 'technical_capability')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

insert into public.rule_catalogue (
  rule_code,
  rule_domain,
  rule_kind,
  rule_version,
  status,
  effective_from,
  effective_until,
  plain_language_explanation,
  owner_role,
  supersedes_rule_id,
  last_reviewed_at
)
values
  ('FEE_STUDIO_1_TO_3_HOUR_BOOKING', 'booking_fee', 'hard_rule', 1, 'active', null, null, 'Studio Space rentals of 1 to 3 hours incur a non-refundable booking fee of EUR 50 excluding VAT.', 'WNC rental point of contact', null, null),
  ('FEE_STUDIO_4_TO_8_HOUR_BOOKING', 'booking_fee', 'hard_rule', 1, 'active', null, null, 'Studio Space rentals of 4 to 8 hours incur a non-refundable booking fee of EUR 75 excluding VAT.', 'WNC rental point of contact', null, null),
  ('FEE_ENTIRE_VENUE_1_TO_3_HOUR_BOOKING', 'booking_fee', 'hard_rule', 1, 'active', null, null, 'Entire Venue rentals of 1 to 3 hours incur a non-refundable booking fee of EUR 100 excluding VAT.', 'WNC rental point of contact', null, null),
  ('FEE_ENTIRE_VENUE_4_TO_7_HOUR_BOOKING', 'booking_fee', 'hard_rule', 1, 'active', null, null, 'Entire Venue rentals of 4 to 7 hours incur a non-refundable booking fee of EUR 250 excluding VAT.', 'WNC rental point of contact', null, null),
  ('FEE_ENTIRE_VENUE_FULL_DAY_BOOKING', 'booking_fee', 'hard_rule', 1, 'active', null, null, 'No booking fee applies to a full-day Entire Venue rental.', 'WNC rental point of contact', null, null),
  ('PAYMENT_UPFRONT_30_PERCENT_OPTION', 'payment', 'hard_rule', 1, 'active', null, null, 'Clients may choose to pay 30 percent of the total rental fee upfront at confirmation only when the rental is being confirmed 15 or more calendar days before the event.', 'WNC rental point of contact', null, null),
  ('PAYMENT_UPFRONT_100_PERCENT_OPTION', 'payment', 'hard_rule', 1, 'active', null, null, 'Clients may choose to pay 100 percent of the total rental fee upfront at confirmation.', 'WNC rental point of contact', null, null),
  ('PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT', 'payment', 'hard_rule', 1, 'active', null, null, 'The rental is confirmed once at least 30 percent of the total rental fee has been received, and payment of that confirmation amount records acceptance of the applicable terms.', 'WNC rental point of contact', null, null),
  ('PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS', 'payment', 'hard_rule', 1, 'active', null, null, 'If 30 percent was paid upfront on a rental confirmed 15 or more calendar days before the event, the remaining 70 percent of the total rental fee is due 14 days before the event.', 'WNC rental point of contact', null, null),
  ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_30_PERCENT', 'payment', 'hard_rule', 1, 'active', null, null, 'For bookings made 15 to 29 days before the event, a 30 percent confirmation payment is due within 3 calendar days.', 'WNC rental point of contact', null, null),
  ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_100_PERCENT', 'payment', 'hard_rule', 1, 'active', null, null, 'For bookings made 15 to 29 days before the event, a 100 percent upfront payment is due within 3 calendar days if that option is chosen.', 'WNC rental point of contact', null, null),
  ('PAYMENT_CONFIRMATION_DEADLINE_0_TO_14_DAYS_100_PERCENT', 'payment', 'hard_rule', 1, 'active', null, null, 'For bookings made 0 to 14 days before the event, a 100 percent upfront payment is due within 24 hours unless a written alternative is approved.', 'WNC rental point of contact', null, null),
  ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'expedited_surcharge', 'hard_rule', 1, 'active', null, null, 'A rental confirmed within 14 calendar days of the event incurs an expedited surcharge equal to 10 percent of the venue rental charge before VAT, subject to 21 percent VAT, and waivable only by the WNC rental point of contact.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS', 'cancellation', 'hard_rule', 1, 'active', null, null, 'When a client cancels more than 30 calendar days before the event, rental payments are refundable.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_BOOKING_FEE_NON_REFUNDABLE', 'cancellation', 'hard_rule', 1, 'active', null, null, 'When a client cancels, the booking fee remains non-refundable.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_PRODUCTION_AND_COORDINATION_FEES_NON_REFUNDABLE', 'cancellation', 'hard_rule', 1, 'active', null, null, 'When a client cancels, agreed production and production-coordination fees remain non-refundable.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_OVER_30_THIRD_PARTY_COMMITTED_COSTS', 'cancellation', 'hard_rule', 1, 'active', null, null, 'When a client cancels more than 30 calendar days before the event, refundable amounts may still be reduced by non-recoverable third-party costs or committed goods, equipment, catering, supplier, or service costs.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_SECURITY_DEPOSIT_RETURNED_UNLESS_DEDUCTIONS', 'cancellation', 'hard_rule', 1, 'active', null, null, 'Cancellation does not remove the standard rule that any security deposit is returned unless valid deductions apply.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_30_OR_FEWER_RENTAL_PAYMENTS', 'cancellation', 'hard_rule', 1, 'active', null, null, 'When a client cancels 30 calendar days or fewer before the event, rental payments are non-refundable.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_30_OR_FEWER_THIRD_PARTY_COMMITTED_COSTS', 'cancellation', 'hard_rule', 1, 'active', null, null, 'When a client cancels 30 calendar days or fewer before the event, the client remains responsible for non-recoverable third-party costs and other committed goods, equipment, catering, supplier, or service costs.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_WNC_REFUND_ALL_FEES_AND_DEPOSITS', 'cancellation', 'hard_rule', 1, 'active', null, null, 'If WNC cancels a rental for reasons unrelated to client breach, all fees and deposits paid are refunded in full.', 'WNC rental point of contact', null, null),
  ('CANCELLATION_CLIENT_BREACH_RETAIN_ALL_PAYMENTS', 'cancellation', 'hard_rule', 1, 'active', null, null, 'If the client breaches the agreement and WNC terminates the rental, WNC may retain all payments already received.', 'WNC rental point of contact', null, null),
  ('CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'capacity', 'hard_rule', 1, 'active', null, null, 'The legal whole-venue guest ceiling is 110 people, but this is not an automatic approval for every event layout.', 'Operations / General Manager', null, null),
  ('CAPACITY_STUDIO_LYING_DOWN', 'capacity', 'hard_rule', 1, 'active', null, null, 'Studio Space supports up to 25 guests for lying-down activities such as sound baths.', 'Operations / General Manager', null, null),
  ('CAPACITY_STUDIO_MOVEMENT', 'capacity', 'hard_rule', 1, 'active', null, null, 'Studio Space supports up to 20 guests for movement-based activities requiring safe spacing.', 'Operations / General Manager', null, null),
  ('CAPACITY_STUDIO_SEATED', 'capacity', 'hard_rule', 1, 'active', null, null, 'Studio Space supports up to 40 guests for a seated layout, subject to furniture, access routes, and the agreed programme.', 'Operations / General Manager', null, null),
  ('CAPACITY_STUDIO_STANDING', 'capacity', 'hard_rule', 1, 'active', null, null, 'Studio Space supports up to 40 guests for a standing layout, subject to layout and circulation.', 'Operations / General Manager', null, null),
  ('CAPACITY_RETAIL_STANDING', 'capacity', 'hard_rule', 1, 'active', null, null, 'The Retail Area supports up to 60 standing guests, including the Conversation Pit within the broader venue layout.', 'Operations / General Manager', null, null),
  ('CAPACITY_ONE_TO_ONE_REQUIRES_CONFIRMATION', 'capacity', 'hard_rule', 1, 'active', null, null, 'The 1:1 / Podcast Room has no fixed published guest capacity and requires explicit confirmation before any guest number is approved.', 'Operations / General Manager', null, null),
  ('CAPACITY_BACK_OFFICE_NOT_EVENT_SPACE', 'capacity', 'hard_rule', 1, 'active', null, null, 'The Back Office is a back-of-house operational space and must not be counted toward guest capacity.', 'Operations / General Manager', null, null),
  ('CAPACITY_STORAGE_ROOM_NOT_EVENT_SPACE', 'capacity', 'hard_rule', 1, 'active', null, null, 'The Storage Room is a restricted operational space and must not be counted toward guest capacity.', 'Operations / General Manager', null, null),
  ('CAPACITY_HALLWAY_BATHROOMS_NOT_EVENT_SPACE', 'capacity', 'hard_rule', 1, 'active', null, null, 'Hallway and bathroom areas provide circulation and facilities only and must not be counted toward guest capacity.', 'Operations / General Manager', null, null),
  ('ACCESS_STUDIO_SPACE_INCLUDED', 'space_access', 'hard_rule', 1, 'active', null, null, 'A Studio Space rental includes exclusive client use of the Studio Space for the agreed hours and approved activity.', 'Operations / General Manager', null, null),
  ('ACCESS_STUDIO_ONE_TO_ONE_INCLUDED', 'space_access', 'hard_rule', 1, 'active', null, null, 'A Studio Space rental includes the 1:1 / Podcast Room by default, although the normal furniture and remaining WNC items may still shape the practical setup.', 'Operations / General Manager', null, null),
  ('ACCESS_STUDIO_RETAIL_SHARED', 'space_access', 'hard_rule', 1, 'active', null, null, 'During a Studio Space rental, the Retail Area remains shared with WNC operations and is not part of the private Studio rental.', 'Operations / General Manager', null, null),
  ('ACCESS_STUDIO_CONVERSATION_PIT_SHARED', 'space_access', 'hard_rule', 1, 'active', null, null, 'During a Studio Space rental, the Conversation Pit follows the Retail Area shared-access rule and is not a separate private rental area.', 'Operations / General Manager', null, null),
  ('ACCESS_STUDIO_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'space_access', 'hard_rule', 1, 'active', null, null, 'During a Studio Space rental, hallway and bathroom areas remain available for access and facilities, but the hallway stays shared.', 'Operations / General Manager', null, null),
  ('ACCESS_STUDIO_BACK_OFFICE_RESTRICTED', 'space_access', 'conditional_rule', 1, 'active', null, null, 'During a Studio Space rental, the Back Office is restricted by default and may be used only where separately agreed and prepared in advance.', 'Operations / General Manager', null, null),
  ('ACCESS_STUDIO_STORAGE_ROOM_RESTRICTED', 'space_access', 'conditional_rule', 1, 'active', null, null, 'During a Studio Space rental, the Storage Room remains WNC-controlled and has no standard client access unless expressly agreed.', 'Operations / General Manager', null, null),
  ('ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED', 'space_access', 'hard_rule', 1, 'active', null, null, 'An Entire Venue rental includes exclusive client use of the Studio Space, subject to the agreed layout and capacity.', 'Operations / General Manager', null, null),
  ('ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'space_access', 'hard_rule', 1, 'active', null, null, 'An Entire Venue rental includes exclusive client use of the Retail Area, including clearing conditions agreed for WNC products and furniture.', 'Operations / General Manager', null, null),
  ('ACCESS_ENTIRE_VENUE_CONVERSATION_PIT_INCLUDED', 'space_access', 'hard_rule', 1, 'active', null, null, 'An Entire Venue rental includes the Conversation Pit as part of the Retail Area, but it is not a separate standalone rental product.', 'Operations / General Manager', null, null),
  ('ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'space_access', 'hard_rule', 1, 'active', null, null, 'An Entire Venue rental includes the 1:1 / Podcast Room by default, although the normal furniture and any remaining WNC items may still shape the practical setup.', 'Operations / General Manager', null, null),
  ('ACCESS_ENTIRE_VENUE_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'space_access', 'hard_rule', 1, 'active', null, null, 'During an Entire Venue rental, hallway and bathroom areas remain available for circulation and facilities, but the hallway remains shared with the building.', 'Operations / General Manager', null, null),
  ('ACCESS_ENTIRE_VENUE_BACK_OFFICE_RESTRICTED', 'space_access', 'conditional_rule', 1, 'active', null, null, 'During an Entire Venue rental, the Back Office is restricted by default and may be included only for a specifically written limited purpose.', 'Operations / General Manager', null, null),
  ('ACCESS_ENTIRE_VENUE_STORAGE_ROOM_RESTRICTED', 'space_access', 'conditional_rule', 1, 'active', null, null, 'During an Entire Venue rental, the Storage Room remains WNC-controlled and must stay available for agreed furniture storage and staff access unless a specific limited arrangement is approved.', 'Operations / General Manager', null, null),
  ('OPER_STUDIO_GRACE_PERIOD', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Studio rentals include a 15 minute grace period before and after the booked time for arrival and departure only; setup is not included.', 'Operations / General Manager', null, null),
  ('OPER_ENTIRE_VENUE_GRACE_PERIOD', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Entire Venue rentals include a 30 minute grace period before and after the booked time for arrival and departure only; setup is not included.', 'Operations / General Manager', null, null),
  ('OPER_SETUP_START_AT_BOOKED_TIME', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Setup and other operational work begin at the booked rental start time unless additional build-up access has been separately booked and approved.', 'Operations / General Manager', null, null),
  ('OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'Earlier setup, unloading, deliveries, or supplier work require separately booked or explicitly approved access and may be declined.', 'Operations / General Manager', null, null),
  ('OPER_OFF_TIMELINE_VISITS_BY_APPOINTMENT', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Visits outside the confirmed rental timeline are by confirmed appointment only.', 'Operations / General Manager', null, null),
  ('OPER_DELIVERIES_WITHIN_RENTAL_WINDOW', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Deliveries and collections must happen inside the confirmed rental timeline unless another access window is explicitly approved.', 'Operations / General Manager', null, null),
  ('OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'External suppliers may access the venue only during the approved access times in the agreed rental timeline.', 'Operations / General Manager', null, null),
  ('OPER_SUPPLIER_INFORMATION_REQUIRED', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Supplier names, timing, access needs, and delivery or collection details must be captured before handover where supplier activity is part of the agreed scope.', 'Operations / General Manager', null, null),
  ('OPER_SUPPLIERS_CLIENT_RESPONSIBILITY', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'The client remains responsible for suppliers unless WNC has explicitly accepted supplier coordination in writing.', 'Operations / General Manager', null, null),
  ('OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'Entire Venue clearing is not automatic. The rooms, products, furniture, reset level, and any moving plan must be agreed explicitly before the rental.', 'Operations / General Manager', null, null),
  ('OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'The Storage Room may be allocated for operational rental storage only through an explicitly agreed arrangement that states what may be stored, for how long, who may access it, and who will collect it.', 'Operations / General Manager', null, null),
  ('OPER_BACK_OFFICE_PREPARATION_REQUIRED', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'Any approved client use of the Back Office requires advance preparation and confirmation because confidential WNC stock and materials must first be secured.', 'Operations / General Manager', null, null),
  ('OPER_MULTI_DAY_TIMELINE_REQUIRED', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Multi-day rentals require one confirmed timeline covering each day''s access, opening, lock-up, cleaning, overnight storage, utilities, and responsibility split.', 'Operations / General Manager', null, null),
  ('OPER_ENTIRE_VENUE_MULTI_DAY_RESET_CLIENT_RESPONSIBILITY', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'For multi-day Entire Venue rentals, the client remains responsible between days for leaving the venue in the agreed condition unless specific WNC cleaning or reset tasks are separately included.', 'Operations / General Manager', null, null),
  ('OPER_INSTALLATION_PLASTER_WALL_FIXINGS_PROHIBITED', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Drilling, nailing, screwing, stapling, or pinning into plaster walls is prohibited.', 'Operations / General Manager', null, null),
  ('OPER_INSTALLATION_STRONG_BOND_ADHESIVES_PROHIBITED', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'Double-sided tape and other strong-bond adhesives are not permitted on venue surfaces.', 'Operations / General Manager', null, null),
  ('OPER_INSTALLATION_REMOVABLE_ADHESIVES_CONDITIONAL', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'Only removable, low-tack, wall-safe adhesive methods may be considered, and they still require prior written approval and testing first.', 'Operations / General Manager', null, null),
  ('OPER_INSTALLATION_WOODEN_BEAM_FIXINGS_CONDITIONAL', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'Small screws or hooks in wooden beams may be used only with prior written approval.', 'Operations / General Manager', null, null),
  ('OPER_INSTALLATION_EXTERIOR_ITEMS_CONDITIONAL', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'Items, build-up, signage, or other operational activity outside the venue boundary require prior written approval and must not be assumed allowed.', 'Operations / General Manager', null, null),
  ('OPER_WASTE_REMOVAL_CLIENT_RESPONSIBILITY', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'The client is responsible for removing packaging, boxes, event materials, supplier waste, and client-provided items during load-out unless another arrangement is agreed.', 'Operations / General Manager', null, null),
  ('OPER_CLEANING_RESET_CLIENT_RESPONSIBILITY', 'operational_requirement', 'hard_rule', 1, 'active', null, null, 'The client is responsible for returning the venue in the handed-over condition unless cleaning or reset support is explicitly included in scope.', 'Operations / General Manager', null, null),
  ('OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', 'operational_requirement', 'conditional_rule', 1, 'active', null, null, 'If the rental involves significant mess, residue, waste, or special effects, professional cleaning must be determined explicitly rather than inferred from a fixed threshold.', 'Operations / General Manager', null, null),
  ('CATER_EXTERNAL_CATERER_ALLOWED', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Clients may use their own external caterer, but the caterer remains subject to venue restrictions, kitchen limits, and the agreed supplier scope.', 'Operations / General Manager', null, null),
  ('CATER_WNC_PARTNER_AVAILABLE', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'A WNC catering-partner option exists, but menu, availability, and practical service needs must still be confirmed for the specific rental.', 'Operations / General Manager', null, null),
  ('CATER_BEVERAGE_PACKAGE_ALLOWED', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'A WNC beverage package may be agreed where the package contents, service method, staffing, and any excluded drinks are confirmed in scope.', 'Operations / General Manager', null, null),
  ('CATER_TAP_WATER_INCLUDED', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Tap water is included for all rentals and does not require a separate catering charge.', 'Operations / General Manager', null, null),
  ('CATER_SPARKLING_WATER_OPTIONAL', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Sparkling water is not included by default. Clients may bring it themselves or WNC may source it where appropriate.', 'Operations / General Manager', null, null),
  ('CATER_EXTERNAL_BARISTA_ALLOWED', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Clients may use their own external barista or bar team, subject to agreed access, venue handover conditions, and any equipment checks.', 'Operations / General Manager', null, null),
  ('CATER_KITCHEN_READY_MADE_SUPPORT', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Where the kitchen or bar is used, WNC supports ready-made food, warming, plating, and light on-site assembly rather than full production cooking.', 'Operations / General Manager', null, null),
  ('CATER_KITCHEN_LARGE_SCALE_PRODUCTION_CONFIRM', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'Large-scale food production is not assumed supported in the WNC kitchen and must be explicitly confirmed before it is promised.', 'Operations / General Manager', null, null),
  ('CATER_EXTERNAL_CATERER_STORAGE_CONFIRM', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'External caterers must confirm any fridge, freezer, dry-storage, or related staging needs before the rental handover is treated as final.', 'Operations / General Manager', null, null),
  ('CATER_EXTERNAL_CATERER_POWER_CONFIRM', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'External caterers must confirm any cooking, warming, or specialist catering equipment that affects venue power or setup.', 'Operations / General Manager', null, null),
  ('CATER_EXTERNAL_BARISTA_STORAGE_CONFIRM', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'External barista or bar teams must confirm milk, stock, and cold-storage needs before the rental handover is final.', 'Operations / General Manager', null, null),
  ('CATER_EXTERNAL_BARISTA_POWER_CONFIRM', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'External barista or bar teams using their own machine must confirm power compatibility before the setup is approved.', 'Operations / General Manager', null, null),
  ('CATER_COFFEE_MACHINE_AGREED_USE', 'catering_supplier', 'conditional_rule', 1, 'active', null, null, 'The WNC coffee machine is available for rental use where agreed and must be used according to the handover instructions.', 'Operations / General Manager', null, null),
  ('CATER_VAT_PRODUCTS_9_PERCENT', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Food and beverage products use the reduced 9 percent VAT category.', 'WNC rental point of contact', null, null),
  ('CATER_VAT_COORDINATION_SERVICE_21_PERCENT', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Catering coordination, preparation, service, and staffing use the standard 21 percent VAT category.', 'WNC rental point of contact', null, null),
  ('CATER_VAT_MIXED_SPLIT_REQUIRED', 'catering_supplier', 'hard_rule', 1, 'active', null, null, 'Mixed catering that includes both products and service must be split into separate proposal or invoice line items rather than one blended VAT rate.', 'WNC rental point of contact', null, null),
  ('TECH_WIFI_STANDARD', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Venue Wi-Fi is a standard included technical capability.', 'Operations / General Manager', null, null),
  ('TECH_BASIC_PROJECTOR_REQUEST_ONLY', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC owns one basic projector that is available on request rather than assumed as a default setup inclusion.', 'Operations / General Manager', null, null),
  ('TECH_PROJECTION_SCREEN_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC does not own a dedicated projection screen, so any dedicated screen requirement needs an external supplier or client-provided solution.', 'Operations / General Manager', null, null),
  ('TECH_SONOS_STANDARD', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'The installed Sonos system is a standard venue capability for ordinary playback and normal sessions.', 'Operations / General Manager', null, null),
  ('TECH_ADDITIONAL_SOUND_SYSTEM_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC does not own an additional production sound system beyond the installed Sonos playback setup.', 'Operations / General Manager', null, null),
  ('TECH_MICROPHONES_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC does not own microphones for rental use.', 'Operations / General Manager', null, null),
  ('TECH_DJ_SETUP_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC does not own a DJ setup for rental use.', 'Operations / General Manager', null, null),
  ('TECH_CASAMBI_LIGHTING_STANDARD', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Casambi dimmable venue lighting is part of the installed standard venue setup.', 'Operations / General Manager', null, null),
  ('TECH_PRODUCTION_LIGHTING_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC does not own specialist production lighting equipment.', 'Operations / General Manager', null, null),
  ('TECH_POWER_GROUPS_STANDARD', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'The venue has 18 electrical groups as part of its standard technical infrastructure, but production-load use still requires checking against the electrical map.', 'Operations / General Manager', null, null),
  ('TECH_VOLTAGE_STANDARD', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Standard venue plug power is 220V per plug.', 'Operations / General Manager', null, null),
  ('TECH_PLUG_POINTS_STANDARD', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Multiple wall plug points are available as standard venue infrastructure, subject to the mapped group layout.', 'Operations / General Manager', null, null),
  ('TECH_EXTENSION_CABLE_REQUEST_ONLY', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC has one basic extension cable available on request; larger or production-grade distribution is not part of the standard venue setup.', 'Operations / General Manager', null, null),
  ('TECH_FILMING_SETUP_NOT_AVAILABLE', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC does not own filming equipment or an internal filming setup.', 'Operations / General Manager', null, null),
  ('TECH_LIVESTREAM_SYSTEM_NOT_AVAILABLE', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'WNC does not own a dedicated livestream system or guaranteed dedicated streaming capacity.', 'Operations / General Manager', null, null),
  ('TECH_REQ_STANDARD_WIFI_SUPPORTED', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Ordinary venue Wi-Fi use is internally supported as a standard venue capability.', 'Operations / General Manager', null, null),
  ('TECH_REQ_ORDINARY_AUDIO_SUPPORTED', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Ordinary venue playback and normal session audio are supported through the installed Sonos system.', 'Operations / General Manager', null, null),
  ('TECH_REQ_AMPLIFIED_SOUND_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Amplified event sound is not internally supported by the installed venue playback system and requires an external supplier or client-provided production solution.', 'Operations / General Manager', null, null),
  ('TECH_REQ_BASIC_PROJECTION_CONFIRM', 'technical_capability', 'conditional_rule', 1, 'active', null, null, 'Basic projection may be possible with the WNC projector, but compatibility, adapters, files, and whether a screenless setup is acceptable must still be confirmed.', 'Operations / General Manager', null, null),
  ('TECH_REQ_PROJECTION_WITH_SCREEN_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Projection that depends on a dedicated screen requires an external supplier or a client-provided screen because WNC does not own one.', 'Operations / General Manager', null, null),
  ('TECH_REQ_MICROPHONE_USE_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Any microphone requirement needs an external or client-provided solution because WNC does not own microphones.', 'Operations / General Manager', null, null),
  ('TECH_REQ_DJ_AUDIO_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'DJ audio is not internally supported by WNC equipment and requires an external supplier or client-provided setup.', 'Operations / General Manager', null, null),
  ('TECH_REQ_STANDARD_LIGHTING_SUPPORTED', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Standard venue lighting is internally supported through the installed Casambi dimmable lighting system.', 'Operations / General Manager', null, null),
  ('TECH_REQ_PRODUCTION_LIGHTING_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Production lighting needs an external supplier or client-provided equipment because WNC does not own specialist production lighting.', 'Operations / General Manager', null, null),
  ('TECH_REQ_STANDARD_POWER_SUPPORTED', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Ordinary venue power access is supported through standard wall plug points and the mapped electrical groups.', 'Operations / General Manager', null, null),
  ('TECH_REQ_HIGH_LOAD_POWER_CONFIRM', 'technical_capability', 'conditional_rule', 1, 'active', null, null, 'High-load or production-power setups require explicit confirmation against the electrical map before support can be promised.', 'Operations / General Manager', null, null),
  ('TECH_REQ_FILMING_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Filming requirements need client-provided or externally supplied equipment because WNC does not own an internal filming setup.', 'Operations / General Manager', null, null),
  ('TECH_REQ_LIVESTREAM_EXTERNAL', 'technical_capability', 'hard_rule', 1, 'active', null, null, 'Dedicated livestreaming requirements need external or client-provided systems because standard venue Wi-Fi does not equal a dedicated livestream setup.', 'Operations / General Manager', null, null),
  ('TECH_REQ_CUSTOM_TECH_CONFIRM', 'technical_capability', 'conditional_rule', 1, 'active', null, null, 'A custom technical setup must be reviewed and confirmed explicitly rather than guessed from the standard venue capabilities.', 'Operations / General Manager', null, null),
  ('SERVICE_LEVEL_VENUE_ONLY', 'service_facilitator', 'hard_rule', 1, 'active', null, null, 'Venue Only is the standard venue-rental service level with venue provision, standard included facilities, and handover, but without added WNC operational or production services.', 'WNC Rental Point of Contact + Operations', null, null),
  ('SERVICE_LEVEL_SUPPORTED_RENTAL', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Supported Rental adds only the specifically agreed WNC support services, staffing periods, and deliverables written into the proposal and agreement.', 'WNC Rental Point of Contact + Operations', null, null),
  ('SERVICE_LEVEL_FULL_PRODUCTION', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Full Production is a broader WNC-managed production service level that must be defined in written scope and manually quoted rather than assumed from venue rental alone.', 'General Manager + WNC Rental Point of Contact', null, null),
  ('SERVICE_ITEM_ONSITE_HOST', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'An On-Site Host is a separately agreed practical venue-support service with quoted hours and duties.', 'Operations / Host Lead', null, null),
  ('SERVICE_ITEM_EVENT_MANAGER', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Event Manager remains a separately agreed on-site coordination role, but final responsibility scope must still be defined explicitly.', 'WNC Rental Point of Contact + Operations', null, null),
  ('SERVICE_ITEM_PRODUCTION_COORDINATION', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Production Coordination is a separately agreed logistics-focused coordination service and not an automatic venue-rental inclusion.', 'WNC Rental Point of Contact + Production Coordinator', null, null),
  ('SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Furniture and Equipment Sourcing is available as a manual coordination service for items beyond WNC standard inventory.', 'WNC Rental Point of Contact + Production Coordinator', null, null),
  ('SERVICE_ITEM_CATERING_COORDINATION', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Catering Coordination is a manual coordination service for catering supplier planning and agreed practical service scope.', 'WNC Rental Point of Contact + Operations', null, null),
  ('SERVICE_ITEM_FACILITATOR_SOURCING', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Facilitator Sourcing is a manual WNC coordination service for facilitator recommendations, availability checks, briefing, and agreed session planning.', 'WNC Rental Point of Contact', null, null),
  ('SERVICE_ITEM_EXPERIENCE_DESIGN', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Experience Design is a separately agreed creative service for guest journey or facilitated experience development.', 'WNC Rental Point of Contact + General Manager / Creative Lead', null, null),
  ('SERVICE_ITEM_SETUP_SUPPORT', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Set-Up Support is separately quoted WNC labour for agreed venue-readiness tasks before the event.', 'Operations / Host Lead', null, null),
  ('SERVICE_ITEM_BREAKDOWN_RESET_SUPPORT', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Breakdown and Reset Support is separately quoted WNC labour for agreed post-event reset tasks.', 'Operations / Host Lead', null, null),
  ('SERVICE_ITEM_CLEANING_SERVICE', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Cleaning can be included only through a specifically agreed cleaning scope or separately invoiced additional cleaning arrangement.', 'Operations', null, null),
  ('SERVICE_ITEM_BEVERAGE_PACKAGE', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'A Beverage Package is an agreed WNC beverage offering whose exact contents, quantities, service method, and staffing must be defined in scope.', 'Operations / Bar Lead', null, null),
  ('SERVICE_ITEM_TECHNICAL_COORDINATION', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Technical Coordination is a separately agreed planning and supplier-coordination service for technical requirements beyond WNC standard basic equipment.', 'WNC Rental Point of Contact + Production Coordinator', null, null),
  ('SERVICE_ITEM_OTHER_SERVICE', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Any other service request must remain an explicit manual scope decision rather than inheriting another service item automatically.', 'WNC Rental Point of Contact', null, null),
  ('FACILITATOR_NONE_NOT_APPLICABLE', 'service_facilitator', 'hard_rule', 1, 'active', null, null, 'When no facilitator arrangement is selected, no facilitator-specific requirement is triggered.', 'WNC Rental Point of Contact', null, null),
  ('FACILITATOR_CLIENT_PROVIDED_ALLOWED', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Client-provided facilitators are allowed, but the client remains responsible and facilitator access, timing, and technical needs still must be captured through the agreed booking scope.', 'WNC Rental Point of Contact', null, null),
  ('FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'A WNC-arranged facilitator cannot be treated as confirmed until availability, scope, timing, and practical requirements are confirmed.', 'WNC Rental Point of Contact', null, null),
  ('FACILITATOR_RECOMMENDATION_REQUESTED_CONFIRMATION_REQUIRED', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'If facilitator recommendations are requested, WNC may source and coordinate options, but facilitator availability and final scope still require confirmation before commitment.', 'WNC Rental Point of Contact', null, null),
  ('FACILITATOR_CUSTOM_EXPERIENCE_DESIGN_MANUAL_REVIEW', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Custom experience-design facilitator requests remain manual-review scope and may not be promised from a fixed catalogue during the current Phase 4 slice.', 'WNC Rental Point of Contact + General Manager / Creative Lead', null, null),
  ('FACILITATOR_UNDER_CONSIDERATION_CONFIRMATION_REQUIRED', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'A facilitator arrangement that is still under consideration must remain uncommitted until the final model, scope, timing, and dependencies are confirmed.', 'WNC Rental Point of Contact', null, null),
  ('FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED', 'service_facilitator', 'conditional_rule', 1, 'active', null, null, 'Unknown facilitator arrangement does not permit the system to infer WNC provision or client provision and must remain confirmation-sensitive.', 'WNC Rental Point of Contact', null, null)
on conflict (rule_code, rule_version) do update
set
  rule_domain = excluded.rule_domain,
  rule_kind = excluded.rule_kind,
  status = excluded.status,
  effective_from = excluded.effective_from,
  effective_until = excluded.effective_until,
  plain_language_explanation = excluded.plain_language_explanation,
  owner_role = excluded.owner_role,
  supersedes_rule_id = excluded.supersedes_rule_id,
  last_reviewed_at = excluded.last_reviewed_at;

insert into public.booking_fee_rules (
  rule_id,
  rental_type_id,
  duration_band_label,
  duration_min_hours,
  duration_max_hours,
  is_fee_charged,
  fee_ex_vat,
  currency_code,
  vat_rate,
  is_refundable,
  waiver_allowed,
  waiver_authority
)
select
  rc.id,
  rt.id,
  seed.duration_band_label,
  seed.duration_min_hours,
  seed.duration_max_hours,
  seed.is_fee_charged,
  seed.fee_ex_vat,
  seed.currency_code,
  seed.vat_rate,
  seed.is_refundable,
  seed.waiver_allowed,
  seed.waiver_authority
from (
  values
    ('FEE_STUDIO_1_TO_3_HOUR_BOOKING', 'studio_space', '1-3 hours', 1, 3, true, 50.00::numeric(12,2), 'EUR', 0.21::numeric(5,4), false, true, 'WNC rental point of contact'),
    ('FEE_STUDIO_4_TO_8_HOUR_BOOKING', 'studio_space', '4-8 hours', 4, 8, true, 75.00::numeric(12,2), 'EUR', 0.21::numeric(5,4), false, true, 'WNC rental point of contact'),
    ('FEE_ENTIRE_VENUE_1_TO_3_HOUR_BOOKING', 'entire_venue', '1-3 hours', 1, 3, true, 100.00::numeric(12,2), 'EUR', 0.21::numeric(5,4), false, true, 'WNC rental point of contact'),
    ('FEE_ENTIRE_VENUE_4_TO_7_HOUR_BOOKING', 'entire_venue', '4-7 hours', 4, 7, true, 250.00::numeric(12,2), 'EUR', 0.21::numeric(5,4), false, true, 'WNC rental point of contact'),
    ('FEE_ENTIRE_VENUE_FULL_DAY_BOOKING', 'entire_venue', 'Full day', 8, 8, false, 0.00::numeric(12,2), 'EUR', 0.21::numeric(5,4), null, null, null)
) as seed(
  rule_code,
  rental_type_code,
  duration_band_label,
  duration_min_hours,
  duration_max_hours,
  is_fee_charged,
  fee_ex_vat,
  currency_code,
  vat_rate,
  is_refundable,
  waiver_allowed,
  waiver_authority
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
join public.rental_types rt
  on rt.rental_type_code = seed.rental_type_code
on conflict (rule_id) do update
set
  rental_type_id = excluded.rental_type_id,
  duration_band_label = excluded.duration_band_label,
  duration_min_hours = excluded.duration_min_hours,
  duration_max_hours = excluded.duration_max_hours,
  is_fee_charged = excluded.is_fee_charged,
  fee_ex_vat = excluded.fee_ex_vat,
  currency_code = excluded.currency_code,
  vat_rate = excluded.vat_rate,
  is_refundable = excluded.is_refundable,
  waiver_allowed = excluded.waiver_allowed,
  waiver_authority = excluded.waiver_authority;

insert into public.payment_rules (
  rule_id,
  payment_stage,
  payment_plan_option,
  percentage_due,
  payment_basis,
  deadline_type,
  deadline_value,
  booking_lead_time_min_days,
  booking_lead_time_max_days,
  required_for_confirmation,
  confirms_booking,
  records_terms_acceptance,
  exception_allowed,
  exception_approver
)
select
  rc.id,
  seed.payment_stage,
  seed.payment_plan_option,
  seed.percentage_due,
  seed.payment_basis,
  seed.deadline_type,
  seed.deadline_value,
  seed.booking_lead_time_min_days,
  seed.booking_lead_time_max_days,
  seed.required_for_confirmation,
  seed.confirms_booking,
  seed.records_terms_acceptance,
  seed.exception_allowed,
  seed.exception_approver
from (
  values
    ('PAYMENT_UPFRONT_30_PERCENT_OPTION', 'upfront_option', 'upfront_30', 30.00::numeric(5,2), 'total_rental_fee', 'at_confirmation', null, 15, null, false, false, false, true, 'WNC rental point of contact'),
    ('PAYMENT_UPFRONT_100_PERCENT_OPTION', 'upfront_option', 'upfront_100', 100.00::numeric(5,2), 'total_rental_fee', 'at_confirmation', null, null, null, false, false, false, true, 'WNC rental point of contact'),
    ('PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT', 'confirmation_requirement', null, 30.00::numeric(5,2), 'total_rental_fee', 'upon_cleared_receipt', null, null, null, true, true, true, false, null),
    ('PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS', 'final_balance', 'upfront_30', 70.00::numeric(5,2), 'total_rental_fee', 'days_before_event', 14, 15, null, false, false, false, true, 'WNC rental point of contact'),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_30_PERCENT', 'confirmation_deadline', 'upfront_30', 30.00::numeric(5,2), 'total_rental_fee', 'days_after_booking', 3, 15, 29, true, false, false, false, null),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_100_PERCENT', 'confirmation_deadline', 'upfront_100', 100.00::numeric(5,2), 'total_rental_fee', 'days_after_booking', 3, 15, 29, true, false, false, false, null),
    ('PAYMENT_CONFIRMATION_DEADLINE_0_TO_14_DAYS_100_PERCENT', 'confirmation_deadline', 'upfront_100', 100.00::numeric(5,2), 'total_rental_fee', 'hours_after_booking', 24, 0, 14, true, false, false, true, 'WNC rental point of contact')
) as seed(
  rule_code,
  payment_stage,
  payment_plan_option,
  percentage_due,
  payment_basis,
  deadline_type,
  deadline_value,
  booking_lead_time_min_days,
  booking_lead_time_max_days,
  required_for_confirmation,
  confirms_booking,
  records_terms_acceptance,
  exception_allowed,
  exception_approver
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
on conflict (rule_id) do update
set
  payment_stage = excluded.payment_stage,
  payment_plan_option = excluded.payment_plan_option,
  percentage_due = excluded.percentage_due,
  payment_basis = excluded.payment_basis,
  deadline_type = excluded.deadline_type,
  deadline_value = excluded.deadline_value,
  booking_lead_time_min_days = excluded.booking_lead_time_min_days,
  booking_lead_time_max_days = excluded.booking_lead_time_max_days,
  required_for_confirmation = excluded.required_for_confirmation,
  confirms_booking = excluded.confirms_booking,
  records_terms_acceptance = excluded.records_terms_acceptance,
  exception_allowed = excluded.exception_allowed,
  exception_approver = excluded.exception_approver;

insert into public.expedited_surcharge_rules (
  rule_id,
  lead_time_min_days,
  lead_time_max_days,
  percentage_rate,
  calculation_basis,
  vat_rate,
  waiver_allowed,
  waiver_authority
)
select
  rc.id,
  seed.lead_time_min_days,
  seed.lead_time_max_days,
  seed.percentage_rate,
  seed.calculation_basis,
  seed.vat_rate,
  seed.waiver_allowed,
  seed.waiver_authority
from (
  values
    ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 0, 14, 0.10::numeric(5,4), 'venue_rental_only', 0.21::numeric(5,4), true, 'WNC rental point of contact')
) as seed(
  rule_code,
  lead_time_min_days,
  lead_time_max_days,
  percentage_rate,
  calculation_basis,
  vat_rate,
  waiver_allowed,
  waiver_authority
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
on conflict (rule_id) do update
set
  lead_time_min_days = excluded.lead_time_min_days,
  lead_time_max_days = excluded.lead_time_max_days,
  percentage_rate = excluded.percentage_rate,
  calculation_basis = excluded.calculation_basis,
  vat_rate = excluded.vat_rate,
  waiver_allowed = excluded.waiver_allowed,
  waiver_authority = excluded.waiver_authority;

insert into public.cancellation_rules (
  rule_id,
  cancellation_scenario,
  cost_category,
  lead_time_min_days,
  lead_time_max_days,
  treatment,
  requires_manual_review
)
select
  rc.id,
  seed.cancellation_scenario,
  seed.cost_category,
  seed.lead_time_min_days,
  seed.lead_time_max_days,
  seed.treatment,
  seed.requires_manual_review
from (
  values
    ('CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS', 'client_cancellation', 'rental_payments', 31, null, 'refundable', false),
    ('CANCELLATION_CLIENT_BOOKING_FEE_NON_REFUNDABLE', 'client_cancellation', 'booking_fee', null, null, 'non_refundable', false),
    ('CANCELLATION_CLIENT_PRODUCTION_AND_COORDINATION_FEES_NON_REFUNDABLE', 'client_cancellation', 'production_and_coordination_fees', null, null, 'non_refundable', false),
    ('CANCELLATION_CLIENT_OVER_30_THIRD_PARTY_COMMITTED_COSTS', 'client_cancellation', 'third_party_committed_costs', 31, null, 'refundable_less_nonrecoverable_costs', true),
    ('CANCELLATION_CLIENT_SECURITY_DEPOSIT_RETURNED_UNLESS_DEDUCTIONS', 'client_cancellation', 'security_deposit', null, null, 'returned_unless_valid_deductions', true),
    ('CANCELLATION_CLIENT_30_OR_FEWER_RENTAL_PAYMENTS', 'client_cancellation', 'rental_payments', 0, 30, 'non_refundable', false),
    ('CANCELLATION_CLIENT_30_OR_FEWER_THIRD_PARTY_COMMITTED_COSTS', 'client_cancellation', 'third_party_committed_costs', 0, 30, 'client_remains_responsible_for_nonrecoverable_costs', true),
    ('CANCELLATION_WNC_REFUND_ALL_FEES_AND_DEPOSITS', 'wnc_cancellation_no_client_breach', 'all_fees_and_deposits', null, null, 'refunded_in_full', false),
    ('CANCELLATION_CLIENT_BREACH_RETAIN_ALL_PAYMENTS', 'client_breach_termination', 'all_payments_received', null, null, 'retained_by_wnc', false)
) as seed(
  rule_code,
  cancellation_scenario,
  cost_category,
  lead_time_min_days,
  lead_time_max_days,
  treatment,
  requires_manual_review
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
on conflict (rule_id) do update
set
  cancellation_scenario = excluded.cancellation_scenario,
  cost_category = excluded.cost_category,
  lead_time_min_days = excluded.lead_time_min_days,
  lead_time_max_days = excluded.lead_time_max_days,
  treatment = excluded.treatment,
  requires_manual_review = excluded.requires_manual_review;

insert into public.capacity_rules (
  rule_id,
  venue_space_id,
  rental_type_id,
  configuration_type,
  capacity_type,
  max_guests,
  requires_confirmation,
  conditions_summary
)
select
  rc.id,
  vs.id,
  rt.id,
  seed.configuration_type,
  seed.capacity_type,
  seed.max_guests,
  seed.requires_confirmation,
  seed.conditions_summary
from (
  values
    ('CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', null, 'entire_venue', null, 'legal_maximum', 110, false, 'Legal ceiling only. Approved event capacity may still be lower depending on activity, setup, and safety requirements.'),
    ('CAPACITY_STUDIO_LYING_DOWN', 'studio_space', null, 'lying_down', 'operational_layout', 25, false, 'Maintain facilitator space and clear circulation for formats such as sound baths.'),
    ('CAPACITY_STUDIO_MOVEMENT', 'studio_space', null, 'movement', 'operational_layout', 20, false, 'Suitable for yoga, movement, and similar sessions requiring personal space.'),
    ('CAPACITY_STUDIO_SEATED', 'studio_space', null, 'seated', 'operational_layout', 40, false, 'Chair availability and the agreed seating layout may still need practical checking.'),
    ('CAPACITY_STUDIO_STANDING', 'studio_space', null, 'standing', 'operational_layout', 40, false, 'Production elements, catering stations, furniture, or circulation requirements may reduce the practical layout.'),
    ('CAPACITY_RETAIL_STANDING', 'retail_area', null, 'standing', 'operational_layout', 60, false, 'The Conversation Pit is part of this area, and usable capacity may fall with service points or production elements.'),
    ('CAPACITY_ONE_TO_ONE_REQUIRES_CONFIRMATION', 'one_to_one_room', null, null, 'must_confirm', null, true, 'No fixed published capacity. Confirm usable space because WNC stores items there and a guest number should not be published until the layout is agreed.'),
    ('CAPACITY_BACK_OFFICE_NOT_EVENT_SPACE', 'back_office', null, null, 'not_event_capacity_space', null, false, 'Operational office, storage, and staff-use space only.'),
    ('CAPACITY_STORAGE_ROOM_NOT_EVENT_SPACE', 'storage_room', null, null, 'not_event_capacity_space', null, false, 'Restricted storage and cleared-furniture space only.'),
    ('CAPACITY_HALLWAY_BATHROOMS_NOT_EVENT_SPACE', 'hallway_bathrooms', null, null, 'not_event_capacity_space', null, false, 'Shared circulation and facility area only.')
) as seed(
  rule_code,
  space_code,
  rental_type_code,
  configuration_type,
  capacity_type,
  max_guests,
  requires_confirmation,
  conditions_summary
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
left join public.venue_spaces vs
  on vs.space_code = seed.space_code
left join public.rental_types rt
  on rt.rental_type_code = seed.rental_type_code
on conflict (rule_id) do update
set
  venue_space_id = excluded.venue_space_id,
  rental_type_id = excluded.rental_type_id,
  configuration_type = excluded.configuration_type,
  capacity_type = excluded.capacity_type,
  max_guests = excluded.max_guests,
  requires_confirmation = excluded.requires_confirmation,
  conditions_summary = excluded.conditions_summary;

insert into public.space_access_rules (
  rule_id,
  rental_type_id,
  venue_space_id,
  access_status,
  access_mode,
  space_function,
  included_by_default,
  requires_preparation,
  requires_confirmation,
  conditions_summary
)
select
  rc.id,
  rt.id,
  vs.id,
  seed.access_status,
  seed.access_mode,
  seed.space_function,
  seed.included_by_default,
  seed.requires_preparation,
  seed.requires_confirmation,
  seed.conditions_summary
from (
  values
    ('ACCESS_STUDIO_SPACE_INCLUDED', 'studio_space', 'studio_space', 'included', 'exclusive_to_client', 'core_event_space', true, false, false, 'Retail / Bar operations may continue outside the Studio, and only the agreed activity, layout, and hours are included.'),
    ('ACCESS_STUDIO_ONE_TO_ONE_INCLUDED', 'studio_space', 'one_to_one_room', 'included', 'client_use_within_agreed_setup', 'flex_space', true, true, false, 'The room is included by default, but existing furniture and any remaining WNC items still shape the agreed setup and usable area.'),
    ('ACCESS_STUDIO_RETAIL_SHARED', 'studio_space', 'retail_area', 'shared', 'shared_with_wnc_operations', 'core_event_space', false, false, false, 'The Retail Area remains operational during Studio rentals and is not part of the client’s private Studio booking.'),
    ('ACCESS_STUDIO_CONVERSATION_PIT_SHARED', 'studio_space', 'conversation_pit', 'shared', 'shared_with_wnc_operations', 'core_event_space', false, false, false, 'The Conversation Pit follows the Retail Area shared-access rule and should not be treated as a separate private Studio-rental area.'),
    ('ACCESS_STUDIO_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'studio_space', 'hallway_bathrooms', 'included', 'shared_circulation_and_facilities', 'circulation_and_facilities', true, false, false, 'Bathrooms are included, and the hallway remains a shared circulation route with the building.'),
    ('ACCESS_STUDIO_BACK_OFFICE_RESTRICTED', 'studio_space', 'back_office', 'restricted', 'wnc_operational_use', 'support_space', false, true, true, 'The Back Office is not part of the standard Studio rental and may be used only where separately agreed and prepared in advance.'),
    ('ACCESS_STUDIO_STORAGE_ROOM_RESTRICTED', 'studio_space', 'storage_room', 'restricted', 'wnc_operational_use', 'support_space', false, false, true, 'The Storage Room remains WNC-controlled and is normally used for WNC storage and venue-clearing items.'),
    ('ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED', 'entire_venue', 'studio_space', 'included', 'exclusive_to_client', 'core_event_space', true, false, false, 'The Studio Space is a core event area in an Entire Venue rental and should be set to the agreed layout.'),
    ('ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'entire_venue', 'retail_area', 'included', 'exclusive_to_client', 'core_event_space', true, true, false, 'The Retail Area is a core event area in an Entire Venue rental. WNC products are cleared from shelves, and furniture clearing may also be agreed if needed.'),
    ('ACCESS_ENTIRE_VENUE_CONVERSATION_PIT_INCLUDED', 'entire_venue', 'conversation_pit', 'included', 'exclusive_to_client', 'core_event_space', true, true, false, 'The Conversation Pit is included as part of the Retail Area in an Entire Venue rental and is not a separate standalone rental area.'),
    ('ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'entire_venue', 'one_to_one_room', 'included', 'client_use_within_agreed_setup', 'flex_space', true, true, false, 'The room is included by default, but existing furniture and any remaining WNC items still shape the agreed setup and any overflow, coat, or facilitator-prep use.'),
    ('ACCESS_ENTIRE_VENUE_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'entire_venue', 'hallway_bathrooms', 'included', 'shared_circulation_and_facilities', 'circulation_and_facilities', true, false, false, 'Bathrooms are included, and the hallway remains a shared building access route rather than private event space.'),
    ('ACCESS_ENTIRE_VENUE_BACK_OFFICE_RESTRICTED', 'entire_venue', 'back_office', 'restricted', 'wnc_operational_use', 'support_space', false, true, true, 'The Back Office is restricted by default and may be included only where a limited purpose is written into the agreed scope.'),
    ('ACCESS_ENTIRE_VENUE_STORAGE_ROOM_RESTRICTED', 'entire_venue', 'storage_room', 'restricted', 'wnc_operational_use', 'support_space', false, true, true, 'The Storage Room is not guest-facing space and must remain WNC-controlled even when furniture clearing or limited client materials are agreed.')
) as seed(
  rule_code,
  rental_type_code,
  space_code,
  access_status,
  access_mode,
  space_function,
  included_by_default,
  requires_preparation,
  requires_confirmation,
  conditions_summary
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
join public.rental_types rt
  on rt.rental_type_code = seed.rental_type_code
join public.venue_spaces vs
  on vs.space_code = seed.space_code
on conflict (rule_id) do update
set
  rental_type_id = excluded.rental_type_id,
  venue_space_id = excluded.venue_space_id,
  access_status = excluded.access_status,
  access_mode = excluded.access_mode,
  space_function = excluded.space_function,
  included_by_default = excluded.included_by_default,
  requires_preparation = excluded.requires_preparation,
  requires_confirmation = excluded.requires_confirmation,
  conditions_summary = excluded.conditions_summary;

insert into public.operational_requirements (
  rule_id,
  rental_type_id,
  venue_space_id,
  requirement_type,
  context_code,
  outcome,
  timing_minutes,
  timing_reference,
  timing_purpose,
  multi_day_scope,
  responsible_party,
  requires_confirmation,
  requires_preparation,
  manual_review_required,
  conditions_summary
)
select
  rc.id,
  rt.id,
  vs.id,
  seed.requirement_type,
  seed.context_code,
  seed.outcome,
  seed.timing_minutes,
  seed.timing_reference,
  seed.timing_purpose,
  seed.multi_day_scope,
  seed.responsible_party,
  seed.requires_confirmation,
  seed.requires_preparation,
  seed.manual_review_required,
  seed.conditions_summary
from (
  values
    ('OPER_STUDIO_GRACE_PERIOD', 'studio_space', null, 'grace_period', 'arrival_departure_only', 'required', 15, 'before_and_after_booked_time', 'arrival_departure_only', 'any', null, false, false, false, 'Arrival and departure buffer only. Setup, unloading, deliveries, and supplier work may not begin during grace time.'),
    ('OPER_ENTIRE_VENUE_GRACE_PERIOD', 'entire_venue', null, 'grace_period', 'arrival_departure_only', 'required', 30, 'before_and_after_booked_time', 'arrival_departure_only', 'any', null, false, false, false, 'Arrival and departure buffer only, including traffic allowance. Setup, unloading, deliveries, and supplier work may not begin during grace time.'),
    ('OPER_SETUP_START_AT_BOOKED_TIME', null, null, 'setup_start', null, 'required', null, 'booked_start_time', null, 'any', null, false, false, false, 'Setup begins at the booked rental start time. If earlier build-up is needed, it must be separately booked or approved rather than inferred from grace time.'),
    ('OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL', null, null, 'early_operational_access', 'approved_timeline_only', 'requires_confirmation', null, 'outside_rental_timeline', null, 'any', null, true, false, false, 'Any earlier setup, unloading, supplier work, or delivery access requires separately booked or explicitly approved access and may be declined.'),
    ('OPER_OFF_TIMELINE_VISITS_BY_APPOINTMENT', null, null, 'off_timeline_visit', 'confirmed_appointment_only', 'requires_confirmation', null, 'outside_rental_timeline', null, 'any', null, true, false, false, 'Visits outside the confirmed rental timeline are by confirmed appointment only.'),
    ('OPER_DELIVERIES_WITHIN_RENTAL_WINDOW', null, null, 'deliveries', 'confirmed_rental_window', 'required', null, 'confirmed_rental_timeline', null, 'any', null, false, false, false, 'Deliveries and collections must happen inside the confirmed rental timeline unless another access window is explicitly approved.'),
    ('OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY', null, null, 'supplier_access', 'approved_timeline_only', 'required', null, 'approved_access_times_only', null, 'any', null, false, false, false, 'External suppliers may access the venue only during the approved access times in the agreed rental timeline.'),
    ('OPER_SUPPLIER_INFORMATION_REQUIRED', null, null, 'supplier_information', null, 'required', null, null, null, 'any', 'client', false, false, false, 'Where supplier activity is part of scope, the client must provide supplier names, timing, access needs, and delivery or collection details before handover.'),
    ('OPER_SUPPLIERS_CLIENT_RESPONSIBILITY', null, null, 'supplier_responsibility', null, 'client_responsibility', null, null, null, 'any', 'client', false, false, false, 'The client manages suppliers unless WNC has explicitly accepted defined coordination responsibility in writing.'),
    ('OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE', 'entire_venue', null, 'venue_clearing', 'full_scope_definition', 'conditional', null, null, null, 'any', null, true, true, false, 'Entire Venue clearing is not automatic. The rooms, products, furniture, reset level, and any moving plan must be agreed explicitly. When included, agreed movable furniture may be moved into the Storage Room.'),
    ('OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL', null, 'storage_room', 'storage_use', 'storage_room_operational_use', 'conditional', null, null, null, 'any', null, true, false, false, 'The Storage Room remains an operational support area. Any event storage arrangement must state what may be stored, for how long, who may access it, and who will collect it.'),
    ('OPER_BACK_OFFICE_PREPARATION_REQUIRED', null, 'back_office', 'back_office_use', 'approved_client_use', 'conditional', null, null, null, 'any', null, true, true, false, 'Any approved client use of the Back Office requires advance preparation because WNC stock and confidential materials must first be secured.'),
    ('OPER_MULTI_DAY_TIMELINE_REQUIRED', null, null, 'multi_day_timeline', 'full_scope_definition', 'required', null, null, null, 'multi_day_only', null, false, false, false, 'Multi-day rentals require one confirmed timeline covering each day''s hours, opening, lock-up, cleaning, overnight storage, utilities, and between-day responsibilities.'),
    ('OPER_ENTIRE_VENUE_MULTI_DAY_RESET_CLIENT_RESPONSIBILITY', 'entire_venue', null, 'multi_day_responsibility', null, 'client_responsibility', null, null, null, 'multi_day_only', 'client', false, false, false, 'For multi-day Entire Venue rentals, the client remains responsible between days for leaving the venue in the agreed condition unless specific WNC cleaning or reset tasks are separately included.'),
    ('OPER_INSTALLATION_PLASTER_WALL_FIXINGS_PROHIBITED', null, null, 'installation', 'plaster_wall_fixings', 'prohibited', null, null, null, 'any', null, false, false, false, 'Drilling, nailing, screwing, stapling, or pinning into plaster walls is prohibited.'),
    ('OPER_INSTALLATION_STRONG_BOND_ADHESIVES_PROHIBITED', null, null, 'installation', 'strong_bond_adhesives', 'prohibited', null, null, null, 'any', null, false, false, false, 'Double-sided tape and other strong-bond adhesives are not permitted on venue surfaces.'),
    ('OPER_INSTALLATION_REMOVABLE_ADHESIVES_CONDITIONAL', null, null, 'installation', 'removable_wall_safe_adhesives', 'conditional', null, null, null, 'any', null, true, false, false, 'Only removable, low-tack, non-marking adhesive methods may be considered, and they still require prior written approval and testing first.'),
    ('OPER_INSTALLATION_WOODEN_BEAM_FIXINGS_CONDITIONAL', null, null, 'installation', 'wooden_beam_fixings', 'conditional', null, null, null, 'any', null, true, false, false, 'Small screws or hooks in wooden beams may be used only with prior written approval.'),
    ('OPER_INSTALLATION_EXTERIOR_ITEMS_CONDITIONAL', null, null, 'installation', 'exterior_items_signage', 'conditional', null, null, null, 'any', null, true, false, false, 'Items, build-up, signage, or other operational activity outside the venue boundary require prior written approval and must not be assumed allowed.'),
    ('OPER_WASTE_REMOVAL_CLIENT_RESPONSIBILITY', null, null, 'waste_removal', null, 'client_responsibility', null, null, null, 'any', 'client', false, false, false, 'The client is responsible for removing packaging, boxes, event materials, supplier waste, and client-provided items during load-out unless another arrangement is agreed.'),
    ('OPER_CLEANING_RESET_CLIENT_RESPONSIBILITY', null, null, 'cleaning_reset', null, 'client_responsibility', null, null, null, 'any', 'client', false, false, false, 'The client is responsible for returning the venue in the handed-over condition unless cleaning or reset support is explicitly included in scope.'),
    ('OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', null, null, 'professional_cleaning', 'significant_mess_or_residue', 'manual_review_required', null, null, null, 'any', null, false, false, true, 'Professional cleaning requirements for significant mess, residue, waste, or special effects must be determined explicitly rather than inferred from an unapproved threshold.')
) as seed(
  rule_code,
  rental_type_code,
  space_code,
  requirement_type,
  context_code,
  outcome,
  timing_minutes,
  timing_reference,
  timing_purpose,
  multi_day_scope,
  responsible_party,
  requires_confirmation,
  requires_preparation,
  manual_review_required,
  conditions_summary
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
left join public.rental_types rt
  on rt.rental_type_code = seed.rental_type_code
left join public.venue_spaces vs
  on vs.space_code = seed.space_code
on conflict (rule_id) do update
set
  rental_type_id = excluded.rental_type_id,
  venue_space_id = excluded.venue_space_id,
  requirement_type = excluded.requirement_type,
  context_code = excluded.context_code,
  outcome = excluded.outcome,
  timing_minutes = excluded.timing_minutes,
  timing_reference = excluded.timing_reference,
  timing_purpose = excluded.timing_purpose,
  multi_day_scope = excluded.multi_day_scope,
  responsible_party = excluded.responsible_party,
  requires_confirmation = excluded.requires_confirmation,
  requires_preparation = excluded.requires_preparation,
  manual_review_required = excluded.manual_review_required,
  conditions_summary = excluded.conditions_summary;

insert into public.catering_supplier_rules (
  rule_id,
  catering_arrangement,
  rule_type,
  context_code,
  outcome,
  external_supplier_required,
  included_by_default,
  wnc_coordination_available,
  wnc_coordination_included,
  kitchen_use_scope,
  kitchen_use_status,
  vat_category,
  vat_rate,
  requires_split_lines,
  requires_confirmation,
  manual_review_required,
  conditions_summary
)
select
  rc.id,
  seed.catering_arrangement,
  seed.rule_type,
  seed.context_code,
  seed.outcome,
  seed.external_supplier_required,
  seed.included_by_default,
  seed.wnc_coordination_available,
  seed.wnc_coordination_included,
  seed.kitchen_use_scope,
  seed.kitchen_use_status,
  seed.vat_category,
  seed.vat_rate,
  seed.requires_split_lines,
  seed.requires_confirmation,
  seed.manual_review_required,
  seed.conditions_summary
from (
  values
    ('CATER_EXTERNAL_CATERER_ALLOWED', 'external_caterer', 'arrangement_policy', null, 'allowed', true, false, true, false, 'any', null, null, null::numeric(5,4), false, false, false, 'Clients may use their own caterer or catering team, but the arrangement remains subject to venue restrictions, kitchen limits, and the agreed supplier scope.'),
    ('CATER_WNC_PARTNER_AVAILABLE', 'wnc_catering_partner', 'arrangement_policy', null, 'wnc_partner_available', false, false, false, false, 'any', null, null, null::numeric(5,4), false, true, false, 'A current WNC catering-partner option exists through the approved supplier path, but availability, menu, and any warming or on-site preparation needs must still be confirmed per rental.'),
    ('CATER_BEVERAGE_PACKAGE_ALLOWED', 'beverage_package', 'arrangement_policy', null, 'conditional', false, false, false, false, 'any', null, null, null::numeric(5,4), false, true, false, 'A WNC beverage package may be agreed, but the package contents, service method, staffing, and any excluded drinks must be confirmed during rental planning.'),
    ('CATER_TAP_WATER_INCLUDED', 'tap_water', 'beverage_policy', null, 'allowed', false, true, false, false, 'any', null, null, null::numeric(5,4), false, false, false, 'Tap water is included and does not require a separate catering charge.'),
    ('CATER_SPARKLING_WATER_OPTIONAL', 'sparkling_water', 'beverage_policy', null, 'conditional', false, false, true, false, 'any', null, null, null::numeric(5,4), false, false, false, 'Sparkling water is not included by default. The client may bring it directly or WNC may source it where appropriate.'),
    ('CATER_EXTERNAL_BARISTA_ALLOWED', 'external_barista_team', 'arrangement_policy', null, 'allowed', true, false, true, false, 'any', null, null, null::numeric(5,4), false, false, false, 'Clients may use their own team or an external barista company, subject to agreed access, venue handover conditions, and any equipment checks.'),
    ('CATER_KITCHEN_READY_MADE_SUPPORT', null, 'kitchen_use', 'ready_made_warming_plating_only', 'allowed', false, false, false, false, 'requested_only', 'limited_support_only', null, null::numeric(5,4), false, false, false, 'The WNC kitchen and bar are suited to ready-made food, warming, plating, and light on-site assembly rather than full production cooking.'),
    ('CATER_KITCHEN_LARGE_SCALE_PRODUCTION_CONFIRM', null, 'kitchen_use', 'large_scale_food_production', 'requires_confirmation', false, false, false, false, 'requested_only', 'requires_confirmation', null, null::numeric(5,4), false, true, false, 'Large-scale food production is not assumed supported in the WNC kitchen and must be explicitly confirmed before it is promised.'),
    ('CATER_EXTERNAL_CATERER_STORAGE_CONFIRM', 'external_caterer', 'supplier_requirement', 'storage_needs_confirmation', 'requires_confirmation', true, false, false, false, 'any', null, null, null::numeric(5,4), false, true, false, 'Confirm any fridge, freezer, dry-storage, or related staging needs for the caterer before final handover.'),
    ('CATER_EXTERNAL_CATERER_POWER_CONFIRM', 'external_caterer', 'supplier_requirement', 'power_needs_confirmation', 'requires_confirmation', true, false, false, false, 'any', null, null, null::numeric(5,4), false, true, false, 'Confirm any cooking, warming, or specialist catering equipment that affects venue power or setup before approval.'),
    ('CATER_EXTERNAL_BARISTA_STORAGE_CONFIRM', 'external_barista_team', 'supplier_requirement', 'storage_needs_confirmation', 'requires_confirmation', true, false, false, false, 'any', null, null, null::numeric(5,4), false, true, false, 'Confirm milk, stock, and cold-storage needs for the external barista or bar team before final handover.'),
    ('CATER_EXTERNAL_BARISTA_POWER_CONFIRM', 'external_barista_team', 'supplier_requirement', 'power_needs_confirmation', 'requires_confirmation', true, false, false, false, 'any', null, null, null::numeric(5,4), false, true, false, 'If the external barista or bar team brings its own machine, power compatibility must be checked before setup is approved.'),
    ('CATER_COFFEE_MACHINE_AGREED_USE', 'external_barista_team', 'equipment_use', 'machine_access_by_agreement', 'conditional', true, false, false, false, 'any', 'agreed_use_only', null, null::numeric(5,4), false, true, false, 'The WNC coffee machine is available where agreed, and the handover must state whether it is being used, cleared, or replaced by the client''s own setup.'),
    ('CATER_VAT_PRODUCTS_9_PERCENT', null, 'vat_classification', 'food_or_beverage_products', 'allowed', false, false, false, false, 'any', null, 'food_or_beverage_products', 0.09::numeric(5,4), false, false, false, 'Food and beverage products use the reduced 9 percent VAT category.'),
    ('CATER_VAT_COORDINATION_SERVICE_21_PERCENT', null, 'vat_classification', 'coordination_or_service', 'allowed', false, false, false, false, 'any', null, 'coordination_or_service', 0.21::numeric(5,4), false, false, false, 'Catering coordination, preparation, service, and staffing use the standard 21 percent VAT category.'),
    ('CATER_VAT_MIXED_SPLIT_REQUIRED', null, 'vat_classification', 'mixed_catering_split', 'conditional', false, false, false, false, 'any', null, 'mixed_catering_split', null::numeric(5,4), true, false, false, 'Mixed catering that includes both products and service must be split into separate line items so the correct VAT treatment can be applied to each component.')
) as seed(
  rule_code,
  catering_arrangement,
  rule_type,
  context_code,
  outcome,
  external_supplier_required,
  included_by_default,
  wnc_coordination_available,
  wnc_coordination_included,
  kitchen_use_scope,
  kitchen_use_status,
  vat_category,
  vat_rate,
  requires_split_lines,
  requires_confirmation,
  manual_review_required,
  conditions_summary
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
on conflict (rule_id) do update
set
  catering_arrangement = excluded.catering_arrangement,
  rule_type = excluded.rule_type,
  context_code = excluded.context_code,
  outcome = excluded.outcome,
  external_supplier_required = excluded.external_supplier_required,
  included_by_default = excluded.included_by_default,
  wnc_coordination_available = excluded.wnc_coordination_available,
  wnc_coordination_included = excluded.wnc_coordination_included,
  kitchen_use_scope = excluded.kitchen_use_scope,
  kitchen_use_status = excluded.kitchen_use_status,
  vat_category = excluded.vat_category,
  vat_rate = excluded.vat_rate,
  requires_split_lines = excluded.requires_split_lines,
  requires_confirmation = excluded.requires_confirmation,
  manual_review_required = excluded.manual_review_required,
  conditions_summary = excluded.conditions_summary;

insert into public.technical_equipment_inventory (
  equipment_code,
  source_item_code,
  equipment_category,
  equipment_name,
  quantity_numeric,
  quantity_display,
  primary_location,
  availability_status,
  normally_included,
  exact_count_guaranteed,
  source_id,
  source_locator,
  conditions_summary
)
select
  seed.equipment_code,
  seed.source_item_code,
  seed.equipment_category,
  seed.equipment_name,
  seed.quantity_numeric,
  seed.quantity_display,
  seed.primary_location,
  seed.availability_status,
  seed.normally_included,
  seed.exact_count_guaranteed,
  sr.id,
  seed.source_locator,
  seed.conditions_summary
from (
  values
    ('yoga_mats', 'EQ-001', 'wellness_equipment', 'Yoga mats', 30, '30', 'Studio / Storage', 'standard', true, false, 'Included equipment EQ-001', 'Check condition and usable count before large events.'),
    ('meditation_cushions', 'EQ-002', 'wellness_equipment', 'Meditation cushions', 30, '30', 'Studio / Storage', 'standard', true, false, 'Included equipment EQ-002', 'Check condition and usable count before large events.'),
    ('eye_masks', 'EQ-003', 'wellness_equipment', 'Eye masks', 30, '30', 'Studio / Storage', 'standard', true, false, 'Included equipment EQ-003', 'Check cleanliness and usable count before large events.'),
    ('blankets', 'EQ-004', 'wellness_equipment', 'Blankets', 30, '30', 'Studio / Storage', 'available_on_request', true, false, 'Included equipment EQ-004', 'Check clean available quantity before confirming the final setup.'),
    ('glassware', 'EQ-005', 'service_equipment', 'Glassware', null, 'Variable', 'Retail / Bar', 'must_confirm', true, false, 'Included equipment EQ-005', 'Confirm glass type and quantity; specialist or high-volume glassware may require rental.'),
    ('standard_furniture', 'EQ-006', 'furniture', 'Standard WNC furniture', null, 'Current venue setup', 'Throughout venue', 'standard', true, false, 'Included equipment EQ-006', 'Confirm what the client wants kept in place and what should be cleared.'),
    ('cutlery', 'EQ-007', 'service_equipment', 'Cutlery', null, 'Variable', 'Retail / Bar', 'must_confirm', true, false, 'Included equipment EQ-007', 'Confirm quantity and service style; high-volume catering may require supplier rental.'),
    ('basic_projector', 'EQ-008', 'projection', 'Basic projector', 1, '1', 'Studio / WNC storage', 'available_on_request', true, true, 'Included equipment EQ-008', 'No screen owned by WNC; client supplies compatible laptop and adapters unless otherwise agreed.'),
    ('basic_extension_cable', 'EQ-009', 'power', 'Basic extension cable', 1, '1', 'WNC storage', 'available_on_request', true, true, 'Included equipment EQ-009', 'Additional extension cables or production-grade distribution require an external supplier or production coordination.'),
    ('casambi_dimmable_lights', 'EQ-010', 'lighting', 'Casambi dimmable lights', null, 'Installed throughout venue', 'Throughout venue', 'standard', true, true, 'Included equipment EQ-010', 'Venue lighting system only; specialist production lighting is external.'),
    ('sonos_speakers', 'EQ-011', 'sound', 'Sonos speakers', 4, '4', '1 Studio; 2 Retail / Bar; 1 Entrance', 'standard', true, true, 'Included equipment EQ-011', 'For background audio and normal sessions, not full production sound.')
) as seed(
  equipment_code,
  source_item_code,
  equipment_category,
  equipment_name,
  quantity_numeric,
  quantity_display,
  primary_location,
  availability_status,
  normally_included,
  exact_count_guaranteed,
  source_locator,
  conditions_summary
)
join public.source_registry sr
  on sr.source_code = 'OPS-002'
on conflict (equipment_code) do update
set
  source_item_code = excluded.source_item_code,
  equipment_category = excluded.equipment_category,
  equipment_name = excluded.equipment_name,
  quantity_numeric = excluded.quantity_numeric,
  quantity_display = excluded.quantity_display,
  primary_location = excluded.primary_location,
  availability_status = excluded.availability_status,
  normally_included = excluded.normally_included,
  exact_count_guaranteed = excluded.exact_count_guaranteed,
  source_id = excluded.source_id,
  source_locator = excluded.source_locator,
  conditions_summary = excluded.conditions_summary;

insert into public.technical_capability_rules (
  rule_id,
  rule_type,
  technical_area,
  capability_code,
  requirement_code,
  equipment_inventory_id,
  support_status,
  included_in_base_rental,
  internal_equipment_exists,
  internal_support_sufficient,
  client_may_self_organise,
  wnc_can_coordinate,
  coordination_fee_possible,
  requires_confirmation,
  manual_review_required,
  conditions_summary
)
select
  rc.id,
  seed.rule_type,
  seed.technical_area,
  seed.capability_code,
  seed.requirement_code,
  tei.id,
  seed.support_status,
  seed.included_in_base_rental,
  seed.internal_equipment_exists,
  seed.internal_support_sufficient,
  seed.client_may_self_organise,
  seed.wnc_can_coordinate,
  seed.coordination_fee_possible,
  seed.requires_confirmation,
  seed.manual_review_required,
  seed.conditions_summary
from (
  values
    ('TECH_WIFI_STANDARD', 'capability_availability', 'connectivity', 'wifi', null, null, 'standard', true, true, true, false, false, false, false, false, 'Venue Wi-Fi is a standard included capability. This slice does not promise dedicated bandwidth or production streaming performance.'),
    ('TECH_BASIC_PROJECTOR_REQUEST_ONLY', 'capability_availability', 'projection', 'basic_projector', null, 'basic_projector', 'available_on_request', true, true, true, true, true, false, true, false, 'One basic projector exists, but the client must supply compatible files, laptop, and adapters unless another arrangement is agreed.'),
    ('TECH_PROJECTION_SCREEN_EXTERNAL', 'capability_availability', 'projection', 'projection_screen', null, null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'No dedicated projection screen is owned by WNC.'),
    ('TECH_SONOS_STANDARD', 'capability_availability', 'sound', 'installed_sonos_system', null, 'sonos_speakers', 'standard', true, true, true, false, false, false, false, false, 'Installed Sonos speakers support background audio and normal sessions, not full production sound.'),
    ('TECH_ADDITIONAL_SOUND_SYSTEM_EXTERNAL', 'capability_availability', 'sound', 'additional_sound_system', null, null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'Additional event or production sound beyond the installed Sonos system requires an external supplier or client-provided setup.'),
    ('TECH_MICROPHONES_EXTERNAL', 'capability_availability', 'audio', 'microphones', null, null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'WNC does not own microphones for rental use.'),
    ('TECH_DJ_SETUP_EXTERNAL', 'capability_availability', 'audio', 'dj_setup', null, null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'WNC does not own a DJ setup for rental use.'),
    ('TECH_CASAMBI_LIGHTING_STANDARD', 'capability_availability', 'lighting', 'casambi_dimmable_venue_lighting', null, 'casambi_dimmable_lights', 'standard', true, true, true, false, false, false, false, false, 'Installed Casambi lighting is part of the standard venue setup.'),
    ('TECH_PRODUCTION_LIGHTING_EXTERNAL', 'capability_availability', 'lighting', 'production_lighting', null, null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'Specialist production lighting is not owned by WNC.'),
    ('TECH_POWER_GROUPS_STANDARD', 'capability_availability', 'power', 'electrical_groups', null, null, 'standard', true, true, true, false, false, false, true, false, 'The venue has 18 electrical groups, but production-load use must still be checked against the electrical map.'),
    ('TECH_VOLTAGE_STANDARD', 'capability_availability', 'power', 'voltage_220v', null, null, 'standard', true, true, true, false, false, false, false, false, 'Standard venue plug power is 220V per plug.'),
    ('TECH_PLUG_POINTS_STANDARD', 'capability_availability', 'power', 'plug_points', null, null, 'standard', true, true, true, false, false, false, true, false, 'Multiple wall plug points are available, and grouped outlets are shown on the electrical map for technical planning.'),
    ('TECH_EXTENSION_CABLE_REQUEST_ONLY', 'capability_availability', 'power', 'basic_extension_cable', null, 'basic_extension_cable', 'available_on_request', true, true, true, true, true, true, true, false, 'One basic extension cable exists. Additional extension or production-grade distribution is not part of the standard venue setup.'),
    ('TECH_FILMING_SETUP_NOT_AVAILABLE', 'capability_availability', 'filming', 'filming_setup', null, null, 'not_available', false, false, false, true, true, true, true, false, 'WNC does not own filming equipment or an internal filming setup.'),
    ('TECH_LIVESTREAM_SYSTEM_NOT_AVAILABLE', 'capability_availability', 'livestream', 'livestream_system', null, null, 'not_available', false, false, false, true, true, true, true, false, 'WNC does not own a dedicated livestream system or guaranteed dedicated streaming capacity.'),
    ('TECH_REQ_STANDARD_WIFI_SUPPORTED', 'requirement_support', 'connectivity', null, 'standard_wifi', null, 'supported', true, true, true, false, false, false, false, false, 'Standard venue Wi-Fi use is supported as part of the base venue capability.'),
    ('TECH_REQ_ORDINARY_AUDIO_SUPPORTED', 'requirement_support', 'sound', null, 'ordinary_audio_playback', null, 'supported', true, true, true, false, false, false, false, false, 'Ordinary playback and normal session audio are supported through the installed Sonos system.'),
    ('TECH_REQ_AMPLIFIED_SOUND_EXTERNAL', 'requirement_support', 'sound', null, 'amplified_event_sound', null, 'external_supplier_required', false, true, false, true, true, true, true, false, 'Amplified event sound is not internally supported by the installed Sonos playback system.'),
    ('TECH_REQ_BASIC_PROJECTION_CONFIRM', 'requirement_support', 'projection', null, 'basic_projection', null, 'requires_confirmation', true, true, true, true, true, false, true, false, 'Basic projection may be possible with the WNC projector, but compatibility, adapters, files, and whether a screenless setup is acceptable must still be confirmed.'),
    ('TECH_REQ_PROJECTION_WITH_SCREEN_EXTERNAL', 'requirement_support', 'projection', null, 'projection_with_dedicated_screen', null, 'external_supplier_required', false, true, false, true, true, true, true, false, 'A dedicated-screen projection requirement needs an external or client-provided screen because WNC does not own one.'),
    ('TECH_REQ_MICROPHONE_USE_EXTERNAL', 'requirement_support', 'audio', null, 'microphone_use', null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'Any microphone requirement needs a client-provided or externally supplied solution.'),
    ('TECH_REQ_DJ_AUDIO_EXTERNAL', 'requirement_support', 'audio', null, 'dj_audio_setup', null, 'external_supplier_required', false, true, false, true, true, true, true, false, 'DJ audio is not internally supported by the installed venue playback system.'),
    ('TECH_REQ_STANDARD_LIGHTING_SUPPORTED', 'requirement_support', 'lighting', null, 'standard_venue_lighting', null, 'supported', true, true, true, false, false, false, false, false, 'Standard venue lighting is supported through the installed Casambi dimmable lighting system.'),
    ('TECH_REQ_PRODUCTION_LIGHTING_EXTERNAL', 'requirement_support', 'lighting', null, 'production_lighting', null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'Specialist production lighting requires external or client-provided equipment.'),
    ('TECH_REQ_STANDARD_POWER_SUPPORTED', 'requirement_support', 'power', null, 'standard_power_access', null, 'supported', true, true, true, false, false, false, false, false, 'Ordinary venue power access is supported through standard wall plug points and the mapped electrical groups.'),
    ('TECH_REQ_HIGH_LOAD_POWER_CONFIRM', 'requirement_support', 'power', null, 'high_load_power', null, 'requires_confirmation', true, true, true, true, true, false, true, false, 'High-load or production-power use must be checked against the electrical map before support can be promised.'),
    ('TECH_REQ_FILMING_EXTERNAL', 'requirement_support', 'filming', null, 'filming', null, 'external_supplier_required', false, false, false, true, true, true, true, false, 'Filming needs client-provided or externally supplied equipment.'),
    ('TECH_REQ_LIVESTREAM_EXTERNAL', 'requirement_support', 'livestream', null, 'dedicated_livestreaming', null, 'external_supplier_required', false, true, false, true, true, true, true, false, 'Dedicated livestreaming needs external or client-provided systems because standard venue Wi-Fi does not equal a dedicated livestream setup.'),
    ('TECH_REQ_CUSTOM_TECH_CONFIRM', 'requirement_support', 'projection', null, 'custom_technical_setup', null, 'requires_confirmation', false, false, false, true, true, true, true, false, 'A custom technical setup must be reviewed and confirmed explicitly rather than guessed from the standard venue capabilities.')
) as seed(
  rule_code,
  rule_type,
  technical_area,
  capability_code,
  requirement_code,
  equipment_code,
  support_status,
  included_in_base_rental,
  internal_equipment_exists,
  internal_support_sufficient,
  client_may_self_organise,
  wnc_can_coordinate,
  coordination_fee_possible,
  requires_confirmation,
  manual_review_required,
  conditions_summary
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
left join public.technical_equipment_inventory tei
  on tei.equipment_code = seed.equipment_code
on conflict (rule_id) do update
set
  rule_type = excluded.rule_type,
  technical_area = excluded.technical_area,
  capability_code = excluded.capability_code,
  requirement_code = excluded.requirement_code,
  equipment_inventory_id = excluded.equipment_inventory_id,
  support_status = excluded.support_status,
  included_in_base_rental = excluded.included_in_base_rental,
  internal_equipment_exists = excluded.internal_equipment_exists,
  internal_support_sufficient = excluded.internal_support_sufficient,
  client_may_self_organise = excluded.client_may_self_organise,
  wnc_can_coordinate = excluded.wnc_can_coordinate,
  coordination_fee_possible = excluded.coordination_fee_possible,
  requires_confirmation = excluded.requires_confirmation,
  manual_review_required = excluded.manual_review_required,
  conditions_summary = excluded.conditions_summary;

insert into public.service_rules (
  rule_id,
  service_level,
  service_type,
  availability_status,
  included_by_default,
  requires_confirmation,
  requires_written_scope,
  manual_quote_required,
  external_supplier_required,
  client_approval_required,
  wnc_coordination_required,
  manual_review_required,
  conditions_summary
)
select
  rc.id,
  seed.service_level,
  seed.service_type,
  seed.availability_status,
  seed.included_by_default,
  seed.requires_confirmation,
  seed.requires_written_scope,
  seed.manual_quote_required,
  seed.external_supplier_required,
  seed.client_approval_required,
  seed.wnc_coordination_required,
  seed.manual_review_required,
  seed.conditions_summary
from (
  values
    ('SERVICE_LEVEL_VENUE_ONLY', 'venue_only', null, 'available', true, false, false, false, false, true, false, false, 'Standard venue-only rental includes agreed spaces, standard included facilities, Wi-Fi, utilities, and handover, but it excludes extra WNC operational or production services.'),
    ('SERVICE_LEVEL_SUPPORTED_RENTAL', 'supported_rental', null, 'conditional', false, true, true, true, false, true, false, false, 'Supported Rental includes only the specifically named support services, staffing periods, and deliverables written into the proposal and agreement.'),
    ('SERVICE_LEVEL_FULL_PRODUCTION', 'full_production', null, 'conditional', false, true, true, true, false, true, true, false, 'Full Production is broader agreed production support and coordination with manual quote and written-scope requirements.'),
    ('SERVICE_ITEM_ONSITE_HOST', null, 'onsite_host', 'conditional', false, true, true, true, false, true, false, false, 'On-Site Host covers agreed practical venue support only and does not silently include guest management, MC duties, supplier management, or facilitator delivery.'),
    ('SERVICE_ITEM_EVENT_MANAGER', null, 'event_manager', 'manual_review_required', false, true, true, true, false, true, true, true, 'Event Manager exists as a current service item, but final responsibility boundaries still must be defined explicitly because event-management scope remains governance-sensitive.'),
    ('SERVICE_ITEM_PRODUCTION_COORDINATION', null, 'production_coordination', 'conditional', false, true, true, true, false, true, true, false, 'Production Coordination covers agreed logistics-focused coordination only and is not the same as full creative production or unlimited event-management responsibility.'),
    ('SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING', null, 'furniture_equipment_sourcing', 'conditional', false, true, true, true, true, true, true, false, 'Furniture and Equipment Sourcing covers supplier research and coordination for non-standard items; supplier charges, deposits, installation, and technical operation are separate scope items.'),
    ('SERVICE_ITEM_CATERING_COORDINATION', null, 'catering_coordination', 'conditional', false, true, true, true, false, true, true, false, 'Catering Coordination covers supplier coordination and practical catering planning, while catering products, staffing, tableware, cleaning, and waste remain separate agreed scope items.'),
    ('SERVICE_ITEM_FACILITATOR_SOURCING', null, 'facilitator_sourcing', 'conditional', false, true, true, true, true, true, true, false, 'Facilitator Sourcing covers recommendations, availability checks, briefing, fee confirmation, and timing or equipment coordination, but it does not guarantee facilitator availability before confirmation.'),
    ('SERVICE_ITEM_EXPERIENCE_DESIGN', null, 'experience_design', 'conditional', false, true, true, true, false, true, false, false, 'Experience Design covers agreed creative direction and guest-journey development only; supplier goods, execution, and facilitator delivery remain separate scope decisions unless explicitly included.'),
    ('SERVICE_ITEM_SETUP_SUPPORT', null, 'setup_support', 'conditional', false, true, true, true, false, true, false, false, 'Set-Up Support covers agreed venue-readiness tasks and ordinary WNC setup labour only; heavy installation, specialist rigging, and supplier labour are not silently included.'),
    ('SERVICE_ITEM_BREAKDOWN_RESET_SUPPORT', null, 'breakdown_reset_support', 'conditional', false, true, true, true, false, true, false, false, 'Breakdown and Reset Support covers agreed post-event reset work only and does not silently include waste removal, deep cleaning, repair work, or extended storage.'),
    ('SERVICE_ITEM_CLEANING_SERVICE', null, 'cleaning_service', 'conditional', false, true, true, true, false, true, false, false, 'Cleaning is available only through an explicitly agreed cleaning scope or post-event charge and must not be inferred from the venue-only handover baseline.'),
    ('SERVICE_ITEM_BEVERAGE_PACKAGE', null, 'beverage_package', 'conditional', false, true, true, true, false, true, false, false, 'Beverage Package means only the named beverages, quantities, service method, equipment, and staffing defined in the approved package or quote.'),
    ('SERVICE_ITEM_TECHNICAL_COORDINATION', null, 'technical_coordination', 'conditional', false, true, true, true, true, true, true, false, 'Technical Coordination covers planning and supplier coordination for technical requirements beyond WNC standard basic equipment and does not itself include operating specialist systems unless separately staffed.'),
    ('SERVICE_ITEM_OTHER_SERVICE', null, 'other_service', 'manual_review_required', false, true, true, true, false, true, false, true, 'Any other service request must remain an explicit manual scope decision and may not inherit another service item automatically.')
) as seed(
  rule_code,
  service_level,
  service_type,
  availability_status,
  included_by_default,
  requires_confirmation,
  requires_written_scope,
  manual_quote_required,
  external_supplier_required,
  client_approval_required,
  wnc_coordination_required,
  manual_review_required,
  conditions_summary
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
on conflict (rule_id) do update
set
  service_level = excluded.service_level,
  service_type = excluded.service_type,
  availability_status = excluded.availability_status,
  included_by_default = excluded.included_by_default,
  requires_confirmation = excluded.requires_confirmation,
  requires_written_scope = excluded.requires_written_scope,
  manual_quote_required = excluded.manual_quote_required,
  external_supplier_required = excluded.external_supplier_required,
  client_approval_required = excluded.client_approval_required,
  wnc_coordination_required = excluded.wnc_coordination_required,
  manual_review_required = excluded.manual_review_required,
  conditions_summary = excluded.conditions_summary;

insert into public.facilitator_requirement_rules (
  rule_id,
  facilitator_arrangement,
  arrangement_status,
  responsible_party,
  client_commitment_requires_facilitator_confirmation,
  requires_availability_confirmation,
  requires_scope_confirmation,
  requires_technical_confirmation,
  client_provided_allowed,
  wnc_coordination_available,
  wnc_coordination_required,
  requires_confirmation,
  manual_review_required,
  conditions_summary
)
select
  rc.id,
  seed.facilitator_arrangement,
  seed.arrangement_status,
  seed.responsible_party,
  seed.client_commitment_requires_facilitator_confirmation,
  seed.requires_availability_confirmation,
  seed.requires_scope_confirmation,
  seed.requires_technical_confirmation,
  seed.client_provided_allowed,
  seed.wnc_coordination_available,
  seed.wnc_coordination_required,
  seed.requires_confirmation,
  seed.manual_review_required,
  seed.conditions_summary
from (
  values
    ('FACILITATOR_NONE_NOT_APPLICABLE', 'none', 'not_applicable', null, false, false, false, false, false, false, false, false, false, 'No facilitator-specific requirement is triggered when no facilitator arrangement is part of the booking scope.'),
    ('FACILITATOR_CLIENT_PROVIDED_ALLOWED', 'client_provided', 'allowed', 'client', false, false, true, true, true, false, false, true, false, 'Client-provided facilitators are allowed, but the client remains responsible and session timing, venue access, and technical needs still must be captured in the agreed booking scope.'),
    ('FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED', 'wnc_provided', 'conditional', 'wnc', true, true, true, true, false, true, true, true, false, 'A WNC-arranged facilitator cannot be treated as committed until availability, session scope, timing, and practical requirements are confirmed.'),
    ('FACILITATOR_RECOMMENDATION_REQUESTED_CONFIRMATION_REQUIRED', 'recommendation_requested', 'conditional', 'shared', true, true, true, true, false, true, true, true, false, 'Where WNC is asked to recommend facilitators, the arrangement remains confirmation-sensitive until a facilitator is chosen and availability, scope, and practical requirements are confirmed.'),
    ('FACILITATOR_CUSTOM_EXPERIENCE_DESIGN_MANUAL_REVIEW', 'custom_experience_design', 'manual_review_required', 'shared', true, true, true, true, false, true, true, true, true, 'Custom experience-design facilitator requests remain manual-review scope and are outside the deferred individual facilitator catalogue for the current slice.'),
    ('FACILITATOR_UNDER_CONSIDERATION_CONFIRMATION_REQUIRED', 'under_consideration', 'conditional', null, false, false, true, true, false, false, false, true, false, 'A facilitator arrangement that is still under consideration must remain uncommitted until the final model, scope, timing, and dependencies are confirmed.'),
    ('FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED', 'unknown', 'conditional', null, false, false, true, false, false, false, false, true, false, 'Unknown facilitator arrangement preserves uncertainty and does not allow the system to infer WNC provision or client provision.')
) as seed(
  rule_code,
  facilitator_arrangement,
  arrangement_status,
  responsible_party,
  client_commitment_requires_facilitator_confirmation,
  requires_availability_confirmation,
  requires_scope_confirmation,
  requires_technical_confirmation,
  client_provided_allowed,
  wnc_coordination_available,
  wnc_coordination_required,
  requires_confirmation,
  manual_review_required,
  conditions_summary
)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
on conflict (rule_id) do update
set
  facilitator_arrangement = excluded.facilitator_arrangement,
  arrangement_status = excluded.arrangement_status,
  responsible_party = excluded.responsible_party,
  client_commitment_requires_facilitator_confirmation = excluded.client_commitment_requires_facilitator_confirmation,
  requires_availability_confirmation = excluded.requires_availability_confirmation,
  requires_scope_confirmation = excluded.requires_scope_confirmation,
  requires_technical_confirmation = excluded.requires_technical_confirmation,
  client_provided_allowed = excluded.client_provided_allowed,
  wnc_coordination_available = excluded.wnc_coordination_available,
  wnc_coordination_required = excluded.wnc_coordination_required,
  requires_confirmation = excluded.requires_confirmation,
  manual_review_required = excluded.manual_review_required,
  conditions_summary = excluded.conditions_summary;

insert into public.rule_source_links (
  rule_id,
  source_id,
  relation_type,
  citation_locator,
  notes
)
select
  rc.id,
  sr.id,
  seed.relation_type,
  seed.citation_locator,
  seed.notes
from (
  values
    ('FEE_STUDIO_1_TO_3_HOUR_BOOKING', 'COM-001-XLSM', 'primary', 'Booking fees BF-001', 'Primary commercial rule row in supplied xlsm workbook.'),
    ('FEE_STUDIO_1_TO_3_HOUR_BOOKING', 'COM-001-XLSX', 'supporting', 'Booking fees BF-001', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('FEE_STUDIO_1_TO_3_HOUR_BOOKING', 'GOV-002', 'governance', 'Decision Log DEC-008; DEC-013; DEC-014', 'Governance authority for amount, refundability, and waiver authority.'),
    ('FEE_STUDIO_4_TO_8_HOUR_BOOKING', 'COM-001-XLSM', 'primary', 'Booking fees BF-002', 'Primary commercial rule row in supplied xlsm workbook.'),
    ('FEE_STUDIO_4_TO_8_HOUR_BOOKING', 'COM-001-XLSX', 'supporting', 'Booking fees BF-002', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('FEE_STUDIO_4_TO_8_HOUR_BOOKING', 'GOV-002', 'governance', 'Decision Log DEC-009; DEC-013; DEC-014', 'Governance authority for amount, refundability, and waiver authority.'),
    ('FEE_ENTIRE_VENUE_1_TO_3_HOUR_BOOKING', 'COM-001-XLSM', 'primary', 'Booking fees BF-003', 'Primary commercial rule row in supplied xlsm workbook.'),
    ('FEE_ENTIRE_VENUE_1_TO_3_HOUR_BOOKING', 'COM-001-XLSX', 'supporting', 'Booking fees BF-003', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('FEE_ENTIRE_VENUE_1_TO_3_HOUR_BOOKING', 'GOV-002', 'governance', 'Decision Log DEC-010; DEC-013; DEC-014', 'Governance authority for amount, refundability, and waiver authority.'),
    ('FEE_ENTIRE_VENUE_4_TO_7_HOUR_BOOKING', 'COM-001-XLSM', 'primary', 'Booking fees BF-004', 'Primary commercial rule row in supplied xlsm workbook.'),
    ('FEE_ENTIRE_VENUE_4_TO_7_HOUR_BOOKING', 'COM-001-XLSX', 'supporting', 'Booking fees BF-004', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('FEE_ENTIRE_VENUE_4_TO_7_HOUR_BOOKING', 'GOV-002', 'governance', 'Decision Log DEC-011; DEC-013; DEC-014', 'Governance authority for amount, refundability, and waiver authority.'),
    ('FEE_ENTIRE_VENUE_FULL_DAY_BOOKING', 'COM-001-XLSM', 'primary', 'Booking fees BF-005', 'Primary commercial rule row in supplied xlsm workbook.'),
    ('FEE_ENTIRE_VENUE_FULL_DAY_BOOKING', 'COM-001-XLSX', 'supporting', 'Booking fees BF-005', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('FEE_ENTIRE_VENUE_FULL_DAY_BOOKING', 'GOV-002', 'governance', 'Decision Log DEC-012', 'Governance authority for the explicit no-booking-fee rule.'),
    ('PAYMENT_UPFRONT_30_PERCENT_OPTION', 'COM-001-XLSM', 'primary', 'Payment rules PAY-001', 'Primary commercial rule row for the 30 percent upfront option.'),
    ('PAYMENT_UPFRONT_30_PERCENT_OPTION', 'COM-001-XLSX', 'supporting', 'Payment rules PAY-001', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('PAYMENT_UPFRONT_30_PERCENT_OPTION', 'GOV-002', 'governance', 'Decision Log DEC-004', 'Governance authority for the 30 percent upfront option.'),
    ('PAYMENT_UPFRONT_100_PERCENT_OPTION', 'COM-001-XLSM', 'primary', 'Payment rules PAY-001', 'Primary commercial rule row for the 100 percent upfront option.'),
    ('PAYMENT_UPFRONT_100_PERCENT_OPTION', 'COM-001-XLSX', 'supporting', 'Payment rules PAY-001', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('PAYMENT_UPFRONT_100_PERCENT_OPTION', 'GOV-002', 'governance', 'Decision Log DEC-004', 'Governance authority for the 100 percent upfront option.'),
    ('PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT', 'COM-001-XLSM', 'primary', 'Payment rules PAY-002', 'Primary commercial rule row for the confirmation-payment threshold.'),
    ('PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT', 'COM-001-XLSX', 'supporting', 'Payment rules PAY-002', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT', 'GOV-002', 'governance', 'Decision Log DEC-001; DEC-002', 'Governance authority for confirmation and terms-acceptance effects.'),
    ('PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS', 'COM-001-XLSM', 'primary', 'Payment rules PAY-003', 'Primary commercial rule row for the final-balance deadline.'),
    ('PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS', 'COM-001-XLSX', 'supporting', 'Payment rules PAY-003', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('PAYMENT_FINAL_BALANCE_70_PERCENT_14_DAYS', 'GOV-002', 'governance', 'Decision Log DEC-005', 'Governance authority for the 70 percent final balance rule.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_30_PERCENT', 'COM-001-XLSM', 'primary', 'Payment rules PAY-004', 'Primary commercial rule row for the 15 to 29 day confirmation deadline.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_30_PERCENT', 'COM-001-XLSX', 'supporting', 'Payment rules PAY-004', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_30_PERCENT', 'GOV-002', 'governance', 'Decision Log DEC-006', 'Governance authority for the 15 to 29 day confirmation deadline.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_100_PERCENT', 'COM-001-XLSM', 'primary', 'Payment rules PAY-004', 'Primary commercial rule row for the 15 to 29 day full-payment deadline.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_100_PERCENT', 'COM-001-XLSX', 'supporting', 'Payment rules PAY-004', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_15_TO_29_DAYS_100_PERCENT', 'GOV-002', 'governance', 'Decision Log DEC-006', 'Governance authority for the 15 to 29 day full-payment deadline.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_0_TO_14_DAYS_100_PERCENT', 'COM-001-XLSM', 'primary', 'Payment rules PAY-005', 'Primary commercial rule row for the within-14-day full-payment deadline.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_0_TO_14_DAYS_100_PERCENT', 'COM-001-XLSX', 'supporting', 'Payment rules PAY-005', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('PAYMENT_CONFIRMATION_DEADLINE_0_TO_14_DAYS_100_PERCENT', 'GOV-002', 'governance', 'Decision Log DEC-007', 'Governance authority for the within-14-day full-payment deadline.'),
    ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'COM-001-XLSM', 'primary', 'Expedited surcharge ES-001', 'Primary commercial rule row for the expedited surcharge policy.'),
    ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'COM-001-XLSX', 'supporting', 'Expedited surcharge ES-001', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'CF-003', 'supporting', 'Expedited surcharge paragraph', 'Studio terms support the 10 percent venue-rental-only surcharge and written waiver requirement.'),
    ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'CF-005', 'supporting', 'Expedited surcharge paragraph', 'Full Venue terms support the 10 percent venue-rental-only surcharge and waiver discretion.'),
    ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'CF-007', 'supporting', 'Schedule 3 expedited surcharge note', 'Agreement template supports recording the surcharge amount or waiver in the booking schedule.'),
    ('EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'GOV-002', 'governance', 'Decision Log DEC-015; DEC-016; DEC-017; DEC-018; DEC-019', 'Governance authority for trigger, scope, rate, exclusions, VAT, and waiver authority.'),
    ('CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS', 'COM-001-XLSM', 'primary', 'Cancellation rules CR-001', 'Primary commercial row for more-than-30-day client-cancellation rental-payment treatment.'),
    ('CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS', 'COM-001-XLSX', 'supporting', 'Cancellation rules CR-001', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS', 'CF-007', 'supporting', 'Cancellation section', 'Agreement template repeats the more-than-30-day rental-payment refund treatment.'),
    ('CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS', 'GOV-002', 'governance', 'Decision Log DEC-020', 'Governance authority for the more-than-30-day rental-payment refund rule.'),
    ('CANCELLATION_CLIENT_BOOKING_FEE_NON_REFUNDABLE', 'COM-001-XLSM', 'primary', 'Cancellation rules CR-001; CR-002', 'Primary commercial rows state that the booking fee remains non-refundable across both client-cancellation windows.'),
    ('CANCELLATION_CLIENT_BOOKING_FEE_NON_REFUNDABLE', 'COM-001-XLSX', 'supporting', 'Cancellation rules CR-001; CR-002', 'Aligned duplicate rows in supplied xlsx workbook.'),
    ('CANCELLATION_CLIENT_BOOKING_FEE_NON_REFUNDABLE', 'CF-007', 'supporting', 'Cancellation section', 'Agreement template repeats that the booking fee is excluded from refundable client-cancellation amounts.'),
    ('CANCELLATION_CLIENT_BOOKING_FEE_NON_REFUNDABLE', 'GOV-002', 'governance', 'Decision Log DEC-020; DEC-022', 'Governance authority for booking-fee non-refundability across both client-cancellation windows.'),
    ('CANCELLATION_CLIENT_PRODUCTION_AND_COORDINATION_FEES_NON_REFUNDABLE', 'COM-001-XLSM', 'primary', 'Cancellation rules CR-001; CR-002', 'Primary commercial rows state that production fees remain non-refundable once agreed.'),
    ('CANCELLATION_CLIENT_PRODUCTION_AND_COORDINATION_FEES_NON_REFUNDABLE', 'COM-001-XLSX', 'supporting', 'Cancellation rules CR-001; CR-002', 'Aligned duplicate rows in supplied xlsx workbook.'),
    ('CANCELLATION_CLIENT_PRODUCTION_AND_COORDINATION_FEES_NON_REFUNDABLE', 'CF-007', 'supporting', 'Cancellation section', 'Agreement template repeats that agreed production and production-coordination fees are excluded from refundable client-cancellation amounts.'),
    ('CANCELLATION_CLIENT_PRODUCTION_AND_COORDINATION_FEES_NON_REFUNDABLE', 'GOV-002', 'governance', 'Decision Log DEC-021', 'Governance authority for production and production-coordination fee non-refundability once agreed.'),
    ('CANCELLATION_CLIENT_OVER_30_THIRD_PARTY_COMMITTED_COSTS', 'COM-001-XLSM', 'primary', 'Cancellation rules CR-001', 'Primary commercial row states that refundable treatment is reduced by non-recoverable third-party commitments.'),
    ('CANCELLATION_CLIENT_OVER_30_THIRD_PARTY_COMMITTED_COSTS', 'COM-001-XLSX', 'supporting', 'Cancellation rules CR-001', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('CANCELLATION_CLIENT_OVER_30_THIRD_PARTY_COMMITTED_COSTS', 'CF-007', 'supporting', 'Cancellation section', 'Agreement template repeats the deduction of non-recoverable committed costs from refundable client-cancellation amounts.'),
    ('CANCELLATION_CLIENT_OVER_30_THIRD_PARTY_COMMITTED_COSTS', 'GOV-002', 'governance', 'Decision Log DEC-020', 'Governance authority for more-than-30-day non-recoverable-cost treatment.'),
    ('CANCELLATION_CLIENT_SECURITY_DEPOSIT_RETURNED_UNLESS_DEDUCTIONS', 'COM-001-XLSM', 'primary', 'Cancellation rules CR-003', 'Primary commercial row states that the security deposit remains refundable unless valid deductions apply.'),
    ('CANCELLATION_CLIENT_SECURITY_DEPOSIT_RETURNED_UNLESS_DEDUCTIONS', 'COM-001-XLSX', 'supporting', 'Cancellation rules CR-003', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('CANCELLATION_CLIENT_SECURITY_DEPOSIT_RETURNED_UNLESS_DEDUCTIONS', 'CF-003', 'supporting', 'Cancellation section', 'Studio terms repeat the security-deposit treatment inside the cancellation policy.'),
    ('CANCELLATION_CLIENT_SECURITY_DEPOSIT_RETURNED_UNLESS_DEDUCTIONS', 'CF-005', 'supporting', 'Cancellation section', 'Full Venue terms repeat the security-deposit treatment inside the cancellation policy.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_RENTAL_PAYMENTS', 'COM-001-XLSM', 'primary', 'Cancellation rules CR-002', 'Primary commercial row for 30-days-or-fewer client-cancellation rental-payment treatment.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_RENTAL_PAYMENTS', 'COM-001-XLSX', 'supporting', 'Cancellation rules CR-002', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_RENTAL_PAYMENTS', 'CF-007', 'supporting', 'Cancellation section', 'Agreement template repeats that rental payments are non-refundable at 30 days or fewer.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_RENTAL_PAYMENTS', 'GOV-002', 'governance', 'Decision Log DEC-022', 'Governance authority for the 30-days-or-fewer rental-payment non-refundability rule.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_THIRD_PARTY_COMMITTED_COSTS', 'COM-001-XLSM', 'primary', 'Cancellation rules CR-002', 'Primary commercial row states that the client remains responsible for non-recoverable third-party commitments at 30 days or fewer.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_THIRD_PARTY_COMMITTED_COSTS', 'COM-001-XLSX', 'supporting', 'Cancellation rules CR-002', 'Aligned duplicate row in supplied xlsx workbook.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_THIRD_PARTY_COMMITTED_COSTS', 'CF-007', 'supporting', 'Cancellation section', 'Agreement template repeats the continuing responsibility for non-recoverable committed costs.'),
    ('CANCELLATION_CLIENT_30_OR_FEWER_THIRD_PARTY_COMMITTED_COSTS', 'GOV-002', 'governance', 'Decision Log DEC-022', 'Governance authority for the 30-days-or-fewer non-recoverable-cost responsibility rule.'),
    ('CANCELLATION_WNC_REFUND_ALL_FEES_AND_DEPOSITS', 'CF-003', 'primary', 'Cancellation section', 'Studio terms state that WNC cancellation unrelated to client breach requires a full refund of all fees and deposits.'),
    ('CANCELLATION_WNC_REFUND_ALL_FEES_AND_DEPOSITS', 'CF-005', 'supporting', 'Cancellation section', 'Full Venue terms match the WNC-initiated full-refund treatment.'),
    ('CANCELLATION_CLIENT_BREACH_RETAIN_ALL_PAYMENTS', 'CF-003', 'primary', 'Termination for client breach section', 'Studio terms state that WNC may terminate immediately for client breach and retain payments made.'),
    ('CANCELLATION_CLIENT_BREACH_RETAIN_ALL_PAYMENTS', 'CF-005', 'supporting', 'Termination for client breach section', 'Full Venue terms match the client-breach termination treatment.'),
    ('CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-001', 'Primary technical-inventory rule for the whole-venue legal maximum.'),
    ('CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'OPS-001', 'supporting', 'Capacity and standard layout', 'Operations Manual repeats the whole-venue legal maximum and warns that practical approval may be lower.'),
    ('CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'CF-007', 'supporting', 'Event, spaces and permitted use', 'Agreement template repeats that the legal whole-venue capacity is 110 and that approved event capacity may be lower.'),
    ('CAPACITY_STUDIO_LYING_DOWN', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-002', 'Primary technical-inventory rule for the Studio lying-down capacity.'),
    ('CAPACITY_STUDIO_LYING_DOWN', 'OPS-001', 'supporting', 'Capacity and standard layout', 'Operations Manual repeats the Studio lying-down maximum.'),
    ('CAPACITY_STUDIO_MOVEMENT', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-003', 'Primary technical-inventory rule for the Studio movement capacity.'),
    ('CAPACITY_STUDIO_MOVEMENT', 'OPS-001', 'supporting', 'Capacity and standard layout', 'Operations Manual repeats the Studio movement maximum.'),
    ('CAPACITY_STUDIO_SEATED', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-004', 'Primary technical-inventory rule for the Studio seated capacity.'),
    ('CAPACITY_STUDIO_SEATED', 'OPS-001', 'supporting', 'Capacity and standard layout', 'Operations Manual repeats the Studio seated maximum and the need to respect furniture and access constraints.'),
    ('CAPACITY_STUDIO_STANDING', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-005', 'Primary technical-inventory rule for the Studio standing capacity.'),
    ('CAPACITY_STUDIO_STANDING', 'OPS-001', 'supporting', 'Capacity and standard layout', 'Operations Manual repeats the Studio standing maximum and layout/circulation constraints.'),
    ('CAPACITY_RETAIL_STANDING', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-006', 'Primary technical-inventory rule for the Retail Area standing capacity.'),
    ('CAPACITY_RETAIL_STANDING', 'OPS-001', 'supporting', 'Capacity and standard layout', 'Operations Manual repeats the Retail Area standing maximum and includes the Conversation Pit within that area.'),
    ('CAPACITY_ONE_TO_ONE_REQUIRES_CONFIRMATION', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-007', 'Primary technical-inventory rule stating that the 1:1 / Podcast Room has no fixed published guest capacity.'),
    ('CAPACITY_ONE_TO_ONE_REQUIRES_CONFIRMATION', 'OPS-001', 'supporting', 'Space list and approved layout/capacity note', 'Operations Manual states that space use must follow the approved activity, layout, and capacity.'),
    ('CAPACITY_BACK_OFFICE_NOT_EVENT_SPACE', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-008', 'Primary technical-inventory rule stating that the Back Office is not part of event guest capacity.'),
    ('CAPACITY_BACK_OFFICE_NOT_EVENT_SPACE', 'OPS-001', 'supporting', 'Space list and approved layout/capacity note', 'Operations Manual treats controlled operational spaces separately from guest capacity.'),
    ('CAPACITY_STORAGE_ROOM_NOT_EVENT_SPACE', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-009', 'Primary technical-inventory rule stating that the Storage Room is not part of event guest capacity.'),
    ('CAPACITY_STORAGE_ROOM_NOT_EVENT_SPACE', 'OPS-001', 'supporting', 'Space list and approved layout/capacity note', 'Operations Manual treats controlled operational spaces separately from guest capacity.'),
    ('CAPACITY_HALLWAY_BATHROOMS_NOT_EVENT_SPACE', 'OPS-002', 'primary', 'Capacity & Space Use Rules CAP-010', 'Primary technical-inventory rule stating that hallway and bathroom areas are not counted toward event guest capacity.'),
    ('CAPACITY_HALLWAY_BATHROOMS_NOT_EVENT_SPACE', 'OPS-001', 'supporting', 'Capacity and standard layout', 'Operations Manual states that hallway and bathroom access is shared circulation and not private event space.'),
    ('ACCESS_STUDIO_SPACE_INCLUDED', 'OPS-002', 'primary', 'Room access by rental type ACC-001', 'Primary technical-inventory access rule for Studio Space inside a Studio rental.'),
    ('ACCESS_STUDIO_SPACE_INCLUDED', 'OPS-001', 'supporting', 'Studio rental and space table', 'Operations Manual confirms Studio Space is included in studio rentals for the approved activity, layout, and capacity.'),
    ('ACCESS_STUDIO_ONE_TO_ONE_INCLUDED', 'OPS-001', 'primary', '1:1 / Podcast Room access note', 'Operations Manual states that the 1:1 / Podcast Room is usually included in Studio rentals and normally remains in its existing furnished condition unless otherwise agreed.'),
    ('ACCESS_STUDIO_ONE_TO_ONE_INCLUDED', 'OPS-002', 'supporting', 'Room access by rental type ACC-002', 'Technical inventory records default Studio-rental inclusion with agreed setup notes.'),
    ('ACCESS_STUDIO_ONE_TO_ONE_INCLUDED', 'CF-007', 'supporting', 'Schedule 2 spaces table', 'Agreement template still requires the exact scope to be recorded, especially for custom-scope rentals or exceptions.'),
    ('ACCESS_STUDIO_RETAIL_SHARED', 'OPS-002', 'primary', 'Room access by rental type ACC-003', 'Primary technical-inventory access rule for the Retail Area during a Studio rental.'),
    ('ACCESS_STUDIO_RETAIL_SHARED', 'OPS-001', 'supporting', 'Studio rental and Retail Area notes', 'Operations Manual states that the Retail Area remains operational during Studio rentals.'),
    ('ACCESS_STUDIO_RETAIL_SHARED', 'CF-003', 'supporting', 'Studio-only rental', 'Studio terms state that the retail store and bar area remain open to the public during Studio rentals.'),
    ('ACCESS_STUDIO_CONVERSATION_PIT_SHARED', 'OPS-001', 'primary', 'Conversation Pit access note', 'Operations Manual states that the Conversation Pit is part of the Retail Area and not a standalone rental area.'),
    ('ACCESS_STUDIO_CONVERSATION_PIT_SHARED', 'OPS-002', 'supporting', 'Room access by rental type ACC-003', 'Technical inventory groups the Retail / Bar Area and Conversation Pit together for Studio-rental access.'),
    ('ACCESS_STUDIO_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'OPS-002', 'primary', 'Room access by rental type ACC-004', 'Primary technical-inventory access rule for hallway and bathroom access during a Studio rental.'),
    ('ACCESS_STUDIO_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'OPS-001', 'supporting', 'Studio rental and hallway/bathrooms notes', 'Operations Manual states that hallway and bathrooms remain available while the building hallway stays shared.'),
    ('ACCESS_STUDIO_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'CF-007', 'supporting', 'Schedule 2 spaces table', 'Agreement template records hallway and bathrooms as included access while keeping the hallway shared.'),
    ('ACCESS_STUDIO_BACK_OFFICE_RESTRICTED', 'OPS-002', 'primary', 'Room access by rental type ACC-005', 'Primary technical-inventory access rule for Back Office restrictions during a Studio rental.'),
    ('ACCESS_STUDIO_BACK_OFFICE_RESTRICTED', 'OPS-001', 'supporting', 'Back Office restrictions', 'Operations Manual states that the Back Office is restricted by default and requires advance agreement and preparation.'),
    ('ACCESS_STUDIO_STORAGE_ROOM_RESTRICTED', 'OPS-002', 'primary', 'Room access by rental type ACC-006', 'Primary technical-inventory access rule for Storage Room restrictions during a Studio rental.'),
    ('ACCESS_STUDIO_STORAGE_ROOM_RESTRICTED', 'OPS-001', 'supporting', 'Storage Room use', 'Operations Manual states that the Storage Room remains WNC-controlled and must not be treated as guest-facing space by default.'),
    ('ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED', 'OPS-002', 'primary', 'Room access by rental type ACC-007', 'Primary technical-inventory access rule for Studio Space inside an Entire Venue rental.'),
    ('ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED', 'OPS-001', 'supporting', 'Entire-venue rental and space table', 'Operations Manual confirms that the Studio Space is a core event area in an Entire Venue rental.'),
    ('ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'OPS-002', 'primary', 'Room access by rental type ACC-008', 'Primary technical-inventory access rule for the Retail Area inside an Entire Venue rental.'),
    ('ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'OPS-001', 'supporting', 'Entire-venue rental and Retail Area notes', 'Operations Manual confirms that the Retail Area is a core event area in an Entire Venue rental.'),
    ('ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'CF-005', 'supporting', 'Space configuration and inventory', 'Full Venue terms state that in-house items remain unless removal or clearing is specifically agreed.'),
    ('ACCESS_ENTIRE_VENUE_CONVERSATION_PIT_INCLUDED', 'OPS-001', 'primary', 'Conversation Pit access note', 'Operations Manual states that the Conversation Pit is part of the Retail Area commercially and operationally, not a separate standalone rental area.'),
    ('ACCESS_ENTIRE_VENUE_CONVERSATION_PIT_INCLUDED', 'OPS-002', 'supporting', 'Room access by rental type ACC-008', 'Technical inventory groups the Retail / Bar Area and Conversation Pit together for Entire Venue access.'),
    ('ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'OPS-001', 'primary', '1:1 / Podcast Room access note', 'Operations Manual states that the 1:1 / Podcast Room is usually included in Entire Venue rentals and normally keeps its existing furniture unless otherwise agreed.'),
    ('ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'OPS-002', 'supporting', 'Room access by rental type ACC-009', 'Technical inventory records default Entire Venue inclusion with agreed setup notes.'),
    ('ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'CF-007', 'supporting', 'Schedule 2 spaces table', 'Agreement template still requires the exact scope to be recorded, especially for custom-scope rentals or exceptions.'),
    ('ACCESS_ENTIRE_VENUE_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'OPS-001', 'primary', 'Hallway and Bathrooms access rule', 'Operations Manual states that hallway and bathrooms are available with rentals while the building hallway remains shared and not private event space.'),
    ('ACCESS_ENTIRE_VENUE_HALLWAY_BATHROOMS_INCLUDED_FOR_ACCESS', 'CF-007', 'supporting', 'Schedule 2 spaces table', 'Agreement template records hallway and bathrooms as included access while keeping the hallway shared.'),
    ('ACCESS_ENTIRE_VENUE_BACK_OFFICE_RESTRICTED', 'OPS-001', 'primary', 'Back Office restrictions', 'Operations Manual states that the Back Office is restricted by default and may be included only for a limited purpose where written into scope.'),
    ('ACCESS_ENTIRE_VENUE_BACK_OFFICE_RESTRICTED', 'CF-007', 'supporting', 'Schedule 2 spaces table', 'Agreement template treats Back Office access as an explicit included, excluded, or limited-access scope item.'),
    ('ACCESS_ENTIRE_VENUE_STORAGE_ROOM_RESTRICTED', 'OPS-001', 'primary', 'Storage Room use', 'Operations Manual states that the Storage Room remains WNC-controlled even when part of it is allocated to an event.'),
    ('ACCESS_ENTIRE_VENUE_STORAGE_ROOM_RESTRICTED', 'CF-005', 'supporting', 'Space configuration and inventory', 'Full Venue terms state that the Storage Room is not part of the guest-facing rental area and must remain accessible to WNC staff.'),
    ('OPER_STUDIO_GRACE_PERIOD', 'CF-003', 'primary', 'Arrival and departure grace period', 'Studio terms approve a 15 minute pre-arrival and post-rental grace period for settling in and light departure only.'),
    ('OPER_STUDIO_GRACE_PERIOD', 'OPS-001', 'supporting', 'Grace periods table', 'Operations Manual repeats the Studio 15 minute before and after grace rule and its arrival and departure purpose.'),
    ('OPER_STUDIO_GRACE_PERIOD', 'CF-007', 'supporting', 'Schedule 1 grace period note', 'Agreement template states that grace periods are for arrival and departure only and do not permit setup or unloading.'),
    ('OPER_ENTIRE_VENUE_GRACE_PERIOD', 'CF-007', 'primary', 'Schedule 1 grace period note', 'Agreement template states that Entire Venue rentals normally include 30 minutes before and after for arrival and departure only.'),
    ('OPER_ENTIRE_VENUE_GRACE_PERIOD', 'OPS-001', 'supporting', 'Grace periods table', 'Operations Manual repeats the Entire Venue 30 minute before and after grace rule and its arrival and departure purpose.'),
    ('OPER_SETUP_START_AT_BOOKED_TIME', 'CF-007', 'primary', 'Access, build-up, and breakdown clause', 'Agreement template states that setup and operational activity may begin only at the agreed rental or build-up time, and that grace time does not grant setup access.'),
    ('OPER_SETUP_START_AT_BOOKED_TIME', 'CF-003', 'supporting', 'Rental start and access timing', 'Studio terms state that setup, unloading, deliveries, furniture movement, and supplier work may not begin before the official rental start unless approved in writing.'),
    ('OPER_SETUP_START_AT_BOOKED_TIME', 'CF-005', 'supporting', 'Appointment-only access and no early access', 'Full Venue terms state that setup may begin only at the official rental start unless an earlier arrangement is approved.'),
    ('OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL', 'OPS-001', 'primary', 'Build-up and breakdown timeline rules', 'Operations Manual states that setup, unloading, supplier work, and deliveries may begin only at the agreed build-up or rental start time and that additional time cannot be guaranteed.'),
    ('OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL', 'CF-007', 'supporting', 'Access, build-up, and breakdown clause', 'Agreement template states that WNC may decline earlier operational access while classes, cleaning, retail operations, or another booking are still taking place.'),
    ('OPER_OFF_TIMELINE_VISITS_BY_APPOINTMENT', 'CF-007', 'primary', 'Access, build-up, and breakdown clause', 'Agreement template states that visits outside the timeline are by confirmed appointment only.'),
    ('OPER_OFF_TIMELINE_VISITS_BY_APPOINTMENT', 'OPS-001', 'supporting', 'Build-up and breakdown timeline rules', 'Operations Manual repeats the appointment-only rule for visits outside the confirmed timeline.'),
    ('OPER_DELIVERIES_WITHIN_RENTAL_WINDOW', 'CF-003', 'primary', 'Deliveries clause', 'Studio terms state that deliveries take place during the confirmed rental window unless otherwise approved.'),
    ('OPER_DELIVERIES_WITHIN_RENTAL_WINDOW', 'CF-005', 'supporting', 'Appointment-only access and no early access', 'Full Venue terms state that deliveries happen during the confirmed rental window unless another arrangement is approved.'),
    ('OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY', 'CF-007', 'primary', 'Schedule 4 supplier access times', 'Agreement template records supplier and facilitator access times as part of the confirmed booking scope.'),
    ('OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY', 'OPS-001', 'supporting', 'General access and timeline rules', 'Operations Manual states that supplier access follows the approved timeline only.'),
    ('OPER_SUPPLIER_INFORMATION_REQUIRED', 'CF-007', 'primary', 'Schedule 4 supplier details', 'Agreement template requires supplier access windows, contact details, and other scope details to be recorded.'),
    ('OPER_SUPPLIER_INFORMATION_REQUIRED', 'OPS-001', 'supporting', 'Timeline and supplier handling notes', 'Operations Manual requires one consolidated timeline covering deliveries, build-up, supplier access, breakdown, and collection.'),
    ('OPER_SUPPLIERS_CLIENT_RESPONSIBILITY', 'OPS-001', 'primary', 'General access and supplier responsibility', 'Operations Manual states that the client manages suppliers unless WNC has accepted defined responsibility in writing.'),
    ('OPER_SUPPLIERS_CLIENT_RESPONSIBILITY', 'CF-007', 'supporting', 'Client responsibilities and Schedule 4', 'Agreement template states that the client manages suppliers unless WNC has accepted that responsibility in writing.'),
    ('OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE', 'OPS-001', 'primary', 'Venue clearing and furniture movement', 'Operations Manual states that venue clearing is not automatic and that the level of clearing, moved items, and reset expectations must be agreed explicitly.'),
    ('OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE', 'CF-005', 'supporting', 'Space configuration and inventory', 'Full Venue terms state that standard layout remains unless removal or clearing is specifically agreed, and that furniture clearing for full productions requires planning.'),
    ('OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL', 'OPS-001', 'primary', 'Storage Room use', 'Operations Manual states that the Storage Room is the default internal storage location during rental operations and that any event allocation must state access and collection details.'),
    ('OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL', 'CF-005', 'supporting', 'Ice Bath Room and Storage Room', 'Full Venue terms state that the Storage Room is usually reserved for secure storage and staff use rather than guest-facing rental activity.'),
    ('OPER_BACK_OFFICE_PREPARATION_REQUIRED', 'OPS-001', 'primary', 'Back Office restrictions', 'Operations Manual states that the Back Office is not default client use space and that secure WNC materials must be prepared before any approved client access.'),
    ('OPER_BACK_OFFICE_PREPARATION_REQUIRED', 'CF-007', 'supporting', 'Schedule 2 spaces table', 'Agreement template treats Back Office use as an explicit included, excluded, or limited-access scope item.'),
    ('OPER_MULTI_DAY_TIMELINE_REQUIRED', 'OPS-001', 'primary', 'Multi-day events', 'Operations Manual states that multi-day events must record each day''s hours, opening, lock-up, cleaning, overnight storage, utilities, and responsibility split.'),
    ('OPER_MULTI_DAY_TIMELINE_REQUIRED', 'CF-007', 'supporting', 'Schedule 1 timeline table', 'Agreement template requires multi-day timeline details to be recorded in the booking schedule.'),
    ('OPER_ENTIRE_VENUE_MULTI_DAY_RESET_CLIENT_RESPONSIBILITY', 'CF-005', 'primary', 'Multi-day rentals', 'Full Venue terms state that the client remains responsible between days for cleaning and leaving the venue in good condition unless another arrangement is explicitly made.'),
    ('OPER_ENTIRE_VENUE_MULTI_DAY_RESET_CLIENT_RESPONSIBILITY', 'OPS-001', 'supporting', 'Multi-day events', 'Operations Manual requires the between-day responsibility split to be explicitly recorded.'),
    ('OPER_INSTALLATION_PLASTER_WALL_FIXINGS_PROHIBITED', 'OPS-001', 'primary', 'Installations and wall protection', 'Operations Manual prohibits drilling, nailing, screwing, stapling, or pinning into plaster walls.'),
    ('OPER_INSTALLATION_PLASTER_WALL_FIXINGS_PROHIBITED', 'CF-003', 'supporting', 'Venue protection rules', 'Studio terms repeat the plaster-wall fixing prohibition.'),
    ('OPER_INSTALLATION_PLASTER_WALL_FIXINGS_PROHIBITED', 'CF-005', 'supporting', 'Venue protection rules', 'Full Venue terms repeat the plaster-wall fixing prohibition.'),
    ('OPER_INSTALLATION_STRONG_BOND_ADHESIVES_PROHIBITED', 'OPS-001', 'primary', 'Installations and wall protection', 'Operations Manual prohibits double-sided and strong-bond adhesives on venue surfaces.'),
    ('OPER_INSTALLATION_STRONG_BOND_ADHESIVES_PROHIBITED', 'CF-003', 'supporting', 'Venue protection rules', 'Studio terms prohibit strong-bond adhesive methods.'),
    ('OPER_INSTALLATION_REMOVABLE_ADHESIVES_CONDITIONAL', 'OPS-001', 'primary', 'Installations and wall protection', 'Operations Manual allows only removable wall-safe adhesive methods subject to testing and prior written approval.'),
    ('OPER_INSTALLATION_REMOVABLE_ADHESIVES_CONDITIONAL', 'CF-003', 'supporting', 'Venue protection rules', 'Studio terms allow only delicate approved adhesive methods in writing in advance.'),
    ('OPER_INSTALLATION_WOODEN_BEAM_FIXINGS_CONDITIONAL', 'OPS-001', 'primary', 'Installations and wall protection', 'Operations Manual allows only small screws or hooks in wooden beams with prior written approval.'),
    ('OPER_INSTALLATION_WOODEN_BEAM_FIXINGS_CONDITIONAL', 'CF-005', 'supporting', 'Venue protection rules', 'Full Venue terms repeat the wooden-beam approval requirement.'),
    ('OPER_INSTALLATION_EXTERIOR_ITEMS_CONDITIONAL', 'OPS-001', 'primary', 'Exterior boundary rules', 'Operations Manual states that signage, build-up, and operational activity outside the venue boundary require prior written approval and must remain off the public pavement or road.'),
    ('OPER_INSTALLATION_EXTERIOR_ITEMS_CONDITIONAL', 'CF-003', 'supporting', 'Exterior items clause', 'Studio terms state that no items may be placed outside the venue without prior written approval.'),
    ('OPER_WASTE_REMOVAL_CLIENT_RESPONSIBILITY', 'OPS-001', 'primary', 'Waste and load-out', 'Operations Manual states that packaging, boxes, event materials, supplier waste, and client items must be removed during load-out unless another arrangement is agreed.'),
    ('OPER_WASTE_REMOVAL_CLIENT_RESPONSIBILITY', 'CF-003', 'supporting', 'Waste removal clause', 'Studio terms repeat that waste must be removed during load-out unless otherwise agreed.'),
    ('OPER_CLEANING_RESET_CLIENT_RESPONSIBILITY', 'OPS-001', 'primary', 'Cleaning and reset responsibility', 'Operations Manual states that the client returns the venue in the handed-over condition unless cleaning or reset support is included.'),
    ('OPER_CLEANING_RESET_CLIENT_RESPONSIBILITY', 'CF-007', 'supporting', 'Services included and responsibility split', 'Agreement template separates cleaning, breakdown, and reset responsibilities so they are not assumed included.'),
    ('OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', 'CF-005', 'primary', 'Cleaning crew requirement for significant mess', 'Full Venue terms state that significant mess, residue, or special-effects events require an explicitly arranged cleaning plan rather than an assumed standard threshold.'),
    ('OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', 'OPS-001', 'supporting', 'Cleaning and restricted materials', 'Operations Manual states that mandatory-cleaning triggers are still case by case and must be included explicitly rather than derived from an unapproved deterministic threshold.'),
    ('CATER_EXTERNAL_CATERER_ALLOWED', 'SERV-003', 'primary', 'Catering & bar rules CBR-002', 'The catering catalogue states that clients may bring their own caterer or catering team and that direct client management carries no WNC coordination fee.'),
    ('CATER_EXTERNAL_CATERER_ALLOWED', 'CF-007', 'supporting', 'Schedule 2 catering and beverage scope', 'The agreement template records whether catering is delivery only, self-service, staffed service, or another agreed arrangement.'),
    ('CATER_EXTERNAL_CATERER_ALLOWED', 'OPS-001', 'supporting', 'General access and kitchen suitability', 'The Operations Manual requires supplier compliance with the agreed timeline, access rules, kitchen limits, and cleaning boundaries.'),
    ('CATER_WNC_PARTNER_AVAILABLE', 'SERV-003', 'primary', 'Catalogue CB-001 and CB-008', 'The catering catalogue records the current WNC catering partner path through Amelie for prepared bites and juices.'),
    ('CATER_WNC_PARTNER_AVAILABLE', 'CF-007', 'supporting', 'Schedule 2 catering and beverage scope', 'The agreement template requires the exact catering scope to be recorded rather than assumed.'),
    ('CATER_BEVERAGE_PACKAGE_ALLOWED', 'SERV-001', 'primary', 'Services catalogue beverage_package', 'The services catalogue defines Beverage Package as an approved WNC offering with agreed beverages, quantities, service method, equipment, and staffing.'),
    ('CATER_BEVERAGE_PACKAGE_ALLOWED', 'SERV-003', 'supporting', 'Catalogue CB-003', 'The catering catalogue records WNC bar or drink service as a current supplier path, while details are confirmed during planning.'),
    ('CATER_TAP_WATER_INCLUDED', 'SERV-003', 'primary', 'Catering & bar rules CBR-009', 'The catering catalogue states that tap water is always included.'),
    ('CATER_SPARKLING_WATER_OPTIONAL', 'SERV-003', 'primary', 'Catering & bar rules CBR-010', 'The catering catalogue states that sparkling water is not included, but the client may bring it or WNC may source it.'),
    ('CATER_EXTERNAL_BARISTA_ALLOWED', 'SERV-003', 'primary', 'Catering & bar rules CBR-011', 'The catering catalogue states that clients may use their own team or an external barista company.'),
    ('CATER_EXTERNAL_BARISTA_ALLOWED', 'CF-007', 'supporting', 'Schedule 2 catering and beverage scope', 'The agreement template requires the exact beverage-service arrangement and supplier scope to be recorded.'),
    ('CATER_KITCHEN_READY_MADE_SUPPORT', 'SERV-003', 'primary', 'Catering & bar rules CBR-001', 'The catering catalogue states that the kitchen is best suited to ready-made food, warming, plating, and light on-site assembly.'),
    ('CATER_KITCHEN_READY_MADE_SUPPORT', 'OPS-001', 'supporting', 'Waste, cleaning, and restricted materials', 'The Operations Manual reinforces that catering scope must define cleaning and service boundaries around kitchen and bar use.'),
    ('CATER_KITCHEN_LARGE_SCALE_PRODUCTION_CONFIRM', 'SERV-003', 'primary', 'Catering & bar rules CBR-001', 'The catering catalogue limits kitchen suitability and does not support assuming large-scale food production without confirmation.'),
    ('CATER_EXTERNAL_CATERER_STORAGE_CONFIRM', 'SERV-003', 'primary', 'External supplier requirements SUP-TPL-001', 'The external supplier requirements template says external caterers must confirm fridge, freezer, and dry-storage needs.'),
    ('CATER_EXTERNAL_CATERER_POWER_CONFIRM', 'SERV-003', 'primary', 'External supplier requirements SUP-TPL-001', 'The external supplier requirements template says external caterers must confirm any cooking, warming, or specialist equipment needs.'),
    ('CATER_EXTERNAL_BARISTA_STORAGE_CONFIRM', 'SERV-003', 'primary', 'External supplier requirements SUP-TPL-002', 'The external supplier requirements template says external barista teams must confirm milk, stock, and cold-storage needs.'),
    ('CATER_EXTERNAL_BARISTA_POWER_CONFIRM', 'SERV-003', 'primary', 'External supplier requirements SUP-TPL-002', 'The external supplier requirements template says any non-standard machine brought by the barista team must be checked.'),
    ('CATER_COFFEE_MACHINE_AGREED_USE', 'SERV-003', 'primary', 'Catering & bar rules CBR-011 and CBR-012', 'The catering catalogue states that the WNC coffee machine is included where agreed and that external teams or multi-day rentals may instead use another setup by agreement.'),
    ('CATER_VAT_PRODUCTS_9_PERCENT', 'COM-001-XLSM', 'primary', 'VAT categories VAT-007 and VAT-008', 'The commercial master sets food and beverage products at 9 percent VAT.'),
    ('CATER_VAT_PRODUCTS_9_PERCENT', 'COM-001-XLSX', 'supporting', 'VAT categories VAT-007 and VAT-008', 'The supplied xlsx variant matches the product VAT categories.'),
    ('CATER_VAT_PRODUCTS_9_PERCENT', 'CF-007', 'supporting', 'Schedule 3 fee summary', 'The agreement template shows food and beverage products on the 9 percent VAT line.'),
    ('CATER_VAT_COORDINATION_SERVICE_21_PERCENT', 'COM-001-XLSM', 'primary', 'VAT categories VAT-006', 'The commercial master sets catering coordination, preparation, service, and staffing at 21 percent VAT.'),
    ('CATER_VAT_COORDINATION_SERVICE_21_PERCENT', 'COM-001-XLSX', 'supporting', 'VAT categories VAT-006', 'The supplied xlsx variant matches the catering coordination and service VAT category.'),
    ('CATER_VAT_COORDINATION_SERVICE_21_PERCENT', 'CF-003', 'supporting', 'VAT clause', 'The Studio terms state that service and coordination line items use the standard 21 percent VAT rate while food and beverage goods use the reduced rate.'),
    ('CATER_VAT_MIXED_SPLIT_REQUIRED', 'COM-001-XLSM', 'primary', 'VAT categories VAT-009', 'The commercial master states that mixed catering must be split between product and service line items.'),
    ('CATER_VAT_MIXED_SPLIT_REQUIRED', 'COM-001-XLSX', 'supporting', 'VAT categories VAT-009', 'The supplied xlsx variant matches the mixed-catering split rule.'),
    ('CATER_VAT_MIXED_SPLIT_REQUIRED', 'SERV-003', 'supporting', 'Catering & bar rules CBR-013', 'The catering catalogue repeats that food and beverage products and WNC coordination or service must be separated on proposals and invoices.'),
    ('TECH_WIFI_STANDARD', 'OPS-002', 'primary', 'Technical capabilities TC-001', 'The technical capability matrix lists venue Wi-Fi as a standard included capability.'),
    ('TECH_BASIC_PROJECTOR_REQUEST_ONLY', 'OPS-002', 'primary', 'Technical capabilities TC-002; Included equipment EQ-008', 'The technical inventory records one basic projector that is available on request rather than automatically promised.'),
    ('TECH_BASIC_PROJECTOR_REQUEST_ONLY', 'CF-007', 'supporting', 'Client technical compatibility clause', 'The agreement template states that the client is responsible for the compatibility of its own laptop, files, adapters, and third-party equipment.'),
    ('TECH_PROJECTION_SCREEN_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-003', 'The technical capability matrix states that WNC owns no projection screen.'),
    ('TECH_SONOS_STANDARD', 'OPS-002', 'primary', 'Technical capabilities TC-004; Included equipment EQ-011', 'The technical inventory records the installed Sonos system as a standard venue capability for normal playback.'),
    ('TECH_ADDITIONAL_SOUND_SYSTEM_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-005', 'The technical capability matrix states that WNC owns no additional sound system beyond the installed venue playback setup.'),
    ('TECH_MICROPHONES_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-006', 'The technical capability matrix states that WNC owns no microphones.'),
    ('TECH_DJ_SETUP_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-007', 'The technical capability matrix states that WNC owns no DJ setup.'),
    ('TECH_CASAMBI_LIGHTING_STANDARD', 'OPS-002', 'primary', 'Technical capabilities TC-008; Included equipment EQ-010', 'The technical inventory records Casambi dimmable venue lighting as installed standard lighting.'),
    ('TECH_PRODUCTION_LIGHTING_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-009', 'The technical capability matrix states that WNC owns no production lighting.'),
    ('TECH_POWER_GROUPS_STANDARD', 'OPS-002', 'primary', 'Technical capabilities TC-010', 'The technical capability matrix records 18 electrical groups with production-load confirmation requirements.'),
    ('TECH_VOLTAGE_STANDARD', 'OPS-002', 'primary', 'Technical capabilities TC-011', 'The technical capability matrix records standard venue power as 220V per plug.'),
    ('TECH_PLUG_POINTS_STANDARD', 'OPS-002', 'primary', 'Technical capabilities TC-012', 'The technical capability matrix records multiple wall plug points marked on the electrical map.'),
    ('TECH_EXTENSION_CABLE_REQUEST_ONLY', 'OPS-002', 'primary', 'Technical capabilities TC-013; Included equipment EQ-009', 'The technical inventory records one basic extension cable that is available on request.'),
    ('TECH_FILMING_SETUP_NOT_AVAILABLE', 'OPS-002', 'primary', 'Technical capabilities TC-014', 'The technical capability matrix states that WNC owns no filming setup.'),
    ('TECH_LIVESTREAM_SYSTEM_NOT_AVAILABLE', 'OPS-002', 'primary', 'Technical capabilities TC-015', 'The technical capability matrix states that WNC owns no dedicated livestream system or dedicated capacity.'),
    ('TECH_REQ_STANDARD_WIFI_SUPPORTED', 'OPS-002', 'primary', 'Technical capabilities TC-001', 'The technical capability matrix lists venue Wi-Fi as standard.'),
    ('TECH_REQ_ORDINARY_AUDIO_SUPPORTED', 'OPS-002', 'primary', 'Technical capabilities TC-004', 'The technical capability matrix and Sonos notes support ordinary playback and normal session audio.'),
    ('TECH_REQ_AMPLIFIED_SOUND_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-004 and TC-005', 'The installed Sonos system is limited to ordinary playback, while additional sound systems are external.'),
    ('TECH_REQ_BASIC_PROJECTION_CONFIRM', 'OPS-002', 'primary', 'Technical capabilities TC-002', 'The technical capability matrix makes basic projector use request-only and confirmation-sensitive.'),
    ('TECH_REQ_BASIC_PROJECTION_CONFIRM', 'CF-007', 'supporting', 'Client technical compatibility clause', 'The agreement template assigns client responsibility for laptops, files, adapters, and third-party compatibility.'),
    ('TECH_REQ_PROJECTION_WITH_SCREEN_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-002 and TC-003', 'WNC has a basic projector but does not own a dedicated projection screen.'),
    ('TECH_REQ_MICROPHONE_USE_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-006', 'Any microphone requirement needs an external or client-provided solution because WNC owns no microphones.'),
    ('TECH_REQ_DJ_AUDIO_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-004, TC-005, and TC-007', 'Installed Sonos playback does not equal an approved DJ or amplified production audio setup.'),
    ('TECH_REQ_STANDARD_LIGHTING_SUPPORTED', 'OPS-002', 'primary', 'Technical capabilities TC-008', 'The technical capability matrix records installed Casambi lighting as a standard venue capability.'),
    ('TECH_REQ_PRODUCTION_LIGHTING_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-009', 'Production lighting requires an external or client-provided solution because WNC owns none.'),
    ('TECH_REQ_STANDARD_POWER_SUPPORTED', 'OPS-002', 'primary', 'Technical capabilities TC-010 to TC-012', 'The electrical groups, voltage, and plug-point rows support ordinary power access as a standard capability.'),
    ('TECH_REQ_HIGH_LOAD_POWER_CONFIRM', 'OPS-002', 'primary', 'Technical capabilities TC-010 and TC-012', 'Production-load or high-draw setups must be checked against the electrical map before support can be promised.'),
    ('TECH_REQ_FILMING_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-014', 'The technical capability matrix states that filming setup is not owned internally.'),
    ('TECH_REQ_LIVESTREAM_EXTERNAL', 'OPS-002', 'primary', 'Technical capabilities TC-001 and TC-015', 'Standard Wi-Fi exists, but dedicated livestreaming remains external because WNC owns no dedicated system or capacity.'),
    ('TECH_REQ_CUSTOM_TECH_CONFIRM', 'OPS-002', 'primary', 'Technical capabilities matrix header', 'The technical capability matrix is used for discovery calls and feasibility, but custom setups still require explicit review rather than assumptions.'),
    ('SERVICE_LEVEL_VENUE_ONLY', 'SERV-001', 'primary', 'Services catalogue venue_only', 'Primary services-catalogue definition of the Venue Only service level.'),
    ('SERVICE_LEVEL_VENUE_ONLY', 'GOV-003', 'governance', 'Enum Lists service_level', 'Data Dictionary governs the canonical service-level machine value.'),
    ('SERVICE_LEVEL_SUPPORTED_RENTAL', 'SERV-001', 'primary', 'Services catalogue supported_rental', 'Primary services-catalogue definition of the Supported Rental service level.'),
    ('SERVICE_LEVEL_SUPPORTED_RENTAL', 'GOV-003', 'governance', 'Enum Lists service_level', 'Data Dictionary governs the canonical service-level machine value.'),
    ('SERVICE_LEVEL_FULL_PRODUCTION', 'SERV-001', 'primary', 'Services catalogue full_production', 'Primary services-catalogue definition of the Full Production service level.'),
    ('SERVICE_LEVEL_FULL_PRODUCTION', 'GOV-003', 'governance', 'Enum Lists service_level', 'Data Dictionary governs the canonical service-level machine value.'),
    ('SERVICE_ITEM_ONSITE_HOST', 'SERV-001', 'primary', 'Services catalogue onsite_host', 'Primary services-catalogue definition of the On-Site Host service item.'),
    ('SERVICE_ITEM_ONSITE_HOST', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_EVENT_MANAGER', 'SERV-001', 'primary', 'Services catalogue event_manager', 'Primary services-catalogue definition of the Event Manager service item.'),
    ('SERVICE_ITEM_EVENT_MANAGER', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_EVENT_MANAGER', 'GOV-002', 'supporting', 'Decision Log OPEN-014', 'The decision log records that event-management scope is still not fully controlled.'),
    ('SERVICE_ITEM_PRODUCTION_COORDINATION', 'SERV-001', 'primary', 'Services catalogue production_coordination', 'Primary services-catalogue definition of the Production Coordination service item.'),
    ('SERVICE_ITEM_PRODUCTION_COORDINATION', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING', 'SERV-001', 'primary', 'Services catalogue furniture_equipment_sourcing', 'Primary services-catalogue definition of the furniture and equipment sourcing service item.'),
    ('SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_CATERING_COORDINATION', 'SERV-001', 'primary', 'Services catalogue catering_coordination', 'Primary services-catalogue definition of the catering coordination service item.'),
    ('SERVICE_ITEM_CATERING_COORDINATION', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_FACILITATOR_SOURCING', 'SERV-001', 'primary', 'Services catalogue facilitator_sourcing', 'Primary services-catalogue definition of the facilitator sourcing service item.'),
    ('SERVICE_ITEM_FACILITATOR_SOURCING', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_FACILITATOR_SOURCING', 'CF-007', 'supporting', 'Facilitator and supplier coordination clauses', 'The agreement template requires facilitated scope details to be recorded and prevents unconfirmed facilitator promises.'),
    ('SERVICE_ITEM_EXPERIENCE_DESIGN', 'SERV-001', 'primary', 'Services catalogue experience_design', 'Primary services-catalogue definition of the Experience Design service item.'),
    ('SERVICE_ITEM_EXPERIENCE_DESIGN', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_SETUP_SUPPORT', 'SERV-001', 'primary', 'Services catalogue setup_support', 'Primary services-catalogue definition of the Set-Up Support service item.'),
    ('SERVICE_ITEM_SETUP_SUPPORT', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_BREAKDOWN_RESET_SUPPORT', 'SERV-001', 'primary', 'Services catalogue breakdown_reset_support', 'Primary services-catalogue definition of the Breakdown and Reset Support service item.'),
    ('SERVICE_ITEM_BREAKDOWN_RESET_SUPPORT', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_CLEANING_SERVICE', 'SERV-001', 'primary', 'Services catalogue cleaning_service', 'Primary services-catalogue definition of the Cleaning service item.'),
    ('SERVICE_ITEM_CLEANING_SERVICE', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_BEVERAGE_PACKAGE', 'SERV-001', 'primary', 'Services catalogue beverage_package', 'Primary services-catalogue definition of the Beverage Package service item.'),
    ('SERVICE_ITEM_BEVERAGE_PACKAGE', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_TECHNICAL_COORDINATION', 'SERV-001', 'primary', 'Services catalogue technical_coordination', 'Primary services-catalogue definition of the Technical Coordination service item.'),
    ('SERVICE_ITEM_TECHNICAL_COORDINATION', 'GOV-003', 'governance', 'Enum Lists service_type', 'Data Dictionary governs the canonical service-type machine value.'),
    ('SERVICE_ITEM_OTHER_SERVICE', 'GOV-003', 'primary', 'Enum Lists service_type', 'The Data Dictionary includes other_service as a canonical service type for controlled manual-scope handling.'),
    ('SERVICE_ITEM_OTHER_SERVICE', 'CF-007', 'supporting', 'Schedule 2 included services and scope', 'The agreement template makes clear that unlisted services are not included unless explicitly written into scope.'),
    ('FACILITATOR_NONE_NOT_APPLICABLE', 'GOV-003', 'primary', 'Enum Lists facilitator_arrangement', 'The Data Dictionary governs the canonical facilitator-arrangement machine value.'),
    ('FACILITATOR_NONE_NOT_APPLICABLE', 'CF-007', 'supporting', 'Schedule 2 facilitator scope', 'The agreement template treats facilitator scope as explicit rather than assumed.'),
    ('FACILITATOR_CLIENT_PROVIDED_ALLOWED', 'GOV-003', 'primary', 'Enum Lists facilitator_arrangement', 'The Data Dictionary governs the canonical facilitator-arrangement machine value.'),
    ('FACILITATOR_CLIENT_PROVIDED_ALLOWED', 'CF-007', 'supporting', 'Client-appointed suppliers and contractors', 'The agreement template keeps client-appointed facilitators and contractors within the client-managed responsibility model unless WNC accepts another role in writing.'),
    ('FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED', 'GOV-003', 'primary', 'Enum Lists facilitator_arrangement', 'The Data Dictionary governs the canonical facilitator-arrangement machine value.'),
    ('FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED', 'SERV-001', 'supporting', 'Services catalogue facilitator_sourcing', 'The services catalogue says facilitator availability, briefing, fee confirmation, and timing coordination must be checked and that availability is not guaranteed before confirmation.'),
    ('FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED', 'CF-007', 'supporting', 'Facilitator appointment clauses', 'The agreement template records facilitator scope and assumes it must be defined in the confirmed schedule.'),
    ('FACILITATOR_RECOMMENDATION_REQUESTED_CONFIRMATION_REQUIRED', 'GOV-003', 'primary', 'Enum Lists facilitator_arrangement', 'The Data Dictionary governs the canonical facilitator-arrangement machine value.'),
    ('FACILITATOR_RECOMMENDATION_REQUESTED_CONFIRMATION_REQUIRED', 'SERV-001', 'supporting', 'Services catalogue facilitator_sourcing', 'Facilitator recommendations, availability checks, and fee confirmation remain coordination work rather than a guaranteed confirmed facilitator.'),
    ('FACILITATOR_CUSTOM_EXPERIENCE_DESIGN_MANUAL_REVIEW', 'GOV-003', 'primary', 'Enum Lists facilitator_arrangement', 'The Data Dictionary governs the canonical facilitator-arrangement machine value.'),
    ('FACILITATOR_CUSTOM_EXPERIENCE_DESIGN_MANUAL_REVIEW', 'SERV-001', 'supporting', 'Services catalogue experience_design and facilitator_sourcing', 'Custom experience design depends on agreed creative scope and facilitator arrangements rather than a fixed current catalogue.'),
    ('FACILITATOR_UNDER_CONSIDERATION_CONFIRMATION_REQUIRED', 'GOV-003', 'primary', 'Enum Lists facilitator_arrangement', 'The Data Dictionary governs the canonical facilitator-arrangement machine value.'),
    ('FACILITATOR_UNDER_CONSIDERATION_CONFIRMATION_REQUIRED', 'CF-007', 'supporting', 'Schedule 2 facilitator scope', 'The agreement template requires facilitator scope to be confirmed rather than assumed.'),
    ('FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED', 'GOV-003', 'primary', 'Enum Lists facilitator_arrangement', 'The Data Dictionary governs the canonical facilitator-arrangement machine value.'),
    ('FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED', 'CF-007', 'supporting', 'Schedule 2 facilitator scope', 'The agreement template requires facilitator scope to be confirmed rather than assumed.')
) as seed(rule_code, source_code, relation_type, citation_locator, notes)
join public.rule_catalogue rc
  on rc.rule_code = seed.rule_code
 and rc.rule_version = 1
join public.source_registry sr
  on sr.source_code = seed.source_code
on conflict (rule_id, source_id, relation_type) do update
set
  citation_locator = excluded.citation_locator,
  notes = excluded.notes;

-- Phase 5.2D controlled catalogue bootstrap.
-- This seed layer intentionally creates private Storage buckets and
-- repository-governed catalogue records without starting chunking or retrieval.

insert into storage.buckets (
  id,
  name,
  public,
  avif_autodetection,
  type
)
values
  ('rental-knowledge', 'rental-knowledge', false, false, 'STANDARD'),
  ('rental-templates', 'rental-templates', false, false, 'STANDARD')
on conflict (id) do update
set
  name = excluded.name,
  public = excluded.public,
  avif_autodetection = excluded.avif_autodetection,
  type = excluded.type,
  file_size_limit = null,
  allowed_mime_types = null,
  owner = null,
  owner_id = null;

with document_seed (
  document_code,
  canonical_title,
  category_code,
  default_owner_role,
  notes
) as (
  values
    ('GOV-001', 'WNC Rental Knowledge Inventory', 'governance_canonical', null, 'Governed corpus inventory and source-precedence register.'),
    ('GOV-002', 'WNC Rental Policy Decisions & Change Log', 'governance_canonical', null, 'Active governance decision record with known lifecycle wording discrepancy across inventory and source registry.'),
    ('GOV-003', 'WNC Rental Data Dictionary', 'governance_canonical', null, 'Canonical terminology and machine-value authority.'),
    ('CF-001', 'Updated Rental Lookbook 2026', 'client_facing_controlled_document', null, 'Logical current lookbook document. Local export representation is present, but the editable master is not available in the repository.'),
    ('CF-003', 'Studio Rental Terms', 'client_facing_controlled_document', null, 'Current governed Studio terms document. Older export retained separately for provenance only.'),
    ('CF-005', 'Full Venue Rental Terms', 'client_facing_controlled_document', null, 'Current governed Full Venue terms document. Older export retained separately for provenance only.'),
    ('CF-007', 'WNC Rental Agreement Template', 'client_facing_controlled_document', null, 'Controlled agreement template used for confirmed rental scope.'),
    ('OPS-001', 'WNC Venue Rental Operations Manual', 'operational_procedure', null, 'Core internal operating manual with current controlled-draft status.'),
    ('OPS-002', 'WNC Venue Technical & Equipment Inventory', 'technical_venue_reference', null, 'Current technical and venue reference workbook.'),
    ('OPS-003', 'WNC Capacity & Space Use Rules', 'technical_venue_reference', null, 'Embedded governed subdocument currently carried inside the shared OPS-002 workbook.'),
    ('SERV-001', 'WNC Rental Services Catalogue', 'service_supplier_guidance', null, 'Current services catalogue with high service and facilitator overlap.'),
    ('SERV-003', 'WNC Catering, Beverage & Supplier Catalogue', 'service_supplier_guidance', null, 'Current catering and supplier catalogue workbook.'),
    ('SERV-004', 'External Supplier Requirements', 'service_supplier_guidance', null, 'Embedded governed supplier-requirements subdocument currently carried inside the shared SERV-003 workbook.'),
    ('TPL-001', 'Studio Rental Proposal Template', 'proposal_guidance', null, 'Current proposal template guidance for Studio rentals.'),
    ('TPL-002', 'Entire Venue Proposal Template', 'proposal_guidance', null, 'Current proposal template guidance for Entire Venue rentals.'),
    ('TPL-003', 'Custom Scope Proposal Template', 'proposal_guidance', null, 'Current proposal template guidance for custom-scope rentals.'),
    ('TPL-004', 'Production Coordination Proposal Template', 'proposal_guidance', null, 'Current proposal template guidance for production-coordination scope.'),
    ('TPL-005', 'Full Production Proposal Template', 'proposal_guidance', null, 'Current proposal template guidance for full-production scope.'),
    ('TPL-006', 'WNC Rental Email Template Library', 'communication_guidance', null, 'Current communication-template guidance library.'),
    ('TPL-007', 'Discovery Call Checklist', 'operational_procedure', null, 'Current checklist guidance document sharing one physical file with the site-visit checklist.'),
    ('TPL-008', 'Site Visit Checklist', 'operational_procedure', null, 'Current checklist guidance document sharing one physical file with the discovery-call checklist.'),
    ('TPL-009', 'Event Handover Checklist', 'operational_procedure', null, 'Current checklist guidance document sharing one physical file with the final-readiness checklist.'),
    ('TPL-010', 'Final Readiness Checklist', 'operational_procedure', null, 'Current checklist guidance document sharing one physical file with the event-handover checklist.'),
    ('TPL-013', 'Rental Close-Out Checklist', 'operational_procedure', null, 'Current post-event close-out checklist guidance.')
)
insert into public.knowledge_documents (
  document_code,
  canonical_title,
  primary_category_id,
  default_owner_role,
  notes
)
select
  ds.document_code,
  ds.canonical_title,
  kc.id,
  ds.default_owner_role,
  ds.notes
from document_seed ds
join public.knowledge_categories kc
  on kc.category_code = ds.category_code
on conflict (document_code) do update
set
  canonical_title = excluded.canonical_title,
  primary_category_id = excluded.primary_category_id,
  default_owner_role = excluded.default_owner_role,
  notes = excluded.notes;

with corpus_seed (
  document_code,
  corpus_status,
  decision_note
) as (
  values
    ('GOV-001', 'include', 'Approved include document from the Phase 5 source corpus matrix.'),
    ('GOV-002', 'include', 'Approved include document from the Phase 5 source corpus matrix.'),
    ('GOV-003', 'include', 'Approved include document from the Phase 5 source corpus matrix.'),
    ('CF-001', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('CF-003', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('CF-005', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('CF-007', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('OPS-001', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('OPS-002', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('OPS-003', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('SERV-001', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('SERV-003', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('SERV-004', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-001', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-002', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-003', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-004', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-005', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-006', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-007', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-008', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-009', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-010', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.'),
    ('TPL-013', 'include', 'Approved include logical document from the Phase 5 source corpus matrix.')
)
insert into public.knowledge_document_corpus_states (
  document_id,
  corpus_status,
  is_current,
  decision_note
)
select
  kd.id,
  cs.corpus_status,
  true,
  cs.decision_note
from corpus_seed cs
join public.knowledge_documents kd
  on kd.document_code = cs.document_code
on conflict (document_id) where is_current do update
set
  corpus_status = excluded.corpus_status,
  decision_note = excluded.decision_note,
  decided_at = null,
  decided_by_role = null;

with version_seed (
  document_code,
  version_number,
  source_version_label,
  governance_status,
  authority_classification,
  lifecycle_note,
  confidentiality_code,
  version_owner_role
) as (
  values
    ('GOV-001', 1, null, 'active', 'authoritative', 'Current governance inventory document in the approved corpus matrix.', 'internal', null),
    ('GOV-002', 1, null, 'active', 'authoritative', 'Current governance decision record; inventory and source registry use slightly different lifecycle wording.', 'commercially_sensitive', null),
    ('GOV-003', 1, 'Current: controlled Phase 2 draft', 'draft', 'authoritative', 'Current controlled draft with wording discrepancy across inventory, source registry, and workbook overview.', 'internal', null),
    ('CF-001', 1, null, 'active', 'authoritative', 'Current lookbook logical document. Local editable master is unavailable; current export remains linked separately.', 'externally_shareable', null),
    ('CF-003', 1, null, 'active', 'authoritative', 'Current Studio terms document. Older PDF export is retained only for provenance review.', 'externally_shareable', null),
    ('CF-005', 1, null, 'active', 'authoritative', 'Current Full Venue terms document. Older PDF export is retained only for provenance review.', 'externally_shareable', null),
    ('CF-007', 1, null, 'active', 'authoritative', 'Current agreement template used to capture confirmed booking scope.', 'externally_shareable', null),
    ('OPS-001', 1, '0.9: Phase 2 controlled draft', 'draft', 'authoritative', 'Current controlled draft pending operational approval as the effective source set evolves.', 'internal', null),
    ('OPS-002', 1, null, 'active', 'authoritative', 'Current technical and equipment inventory workbook.', 'internal', null),
    ('OPS-003', 1, null, 'active', 'authoritative', 'Current embedded governed capacity and space-use source carried inside the shared OPS-002 workbook.', 'internal', null),
    ('SERV-001', 1, null, 'active', 'authoritative', 'Current services catalogue workbook.', 'commercially_sensitive', null),
    ('SERV-003', 1, null, 'active', 'authoritative', 'Current catering and supplier catalogue workbook.', 'commercially_sensitive', null),
    ('SERV-004', 1, null, 'active', 'authoritative', 'Current embedded supplier-requirements source carried inside the shared SERV-003 workbook.', 'internal', null),
    ('TPL-001', 1, null, 'active', 'guidance', 'Current proposal-guidance template for Studio rentals.', 'commercially_sensitive', null),
    ('TPL-002', 1, null, 'active', 'guidance', 'Current proposal-guidance template for Entire Venue rentals.', 'commercially_sensitive', null),
    ('TPL-003', 1, null, 'active', 'guidance', 'Current proposal-guidance template for custom-scope rentals.', 'commercially_sensitive', null),
    ('TPL-004', 1, null, 'active', 'guidance', 'Current proposal-guidance template for production-coordination scope.', 'commercially_sensitive', null),
    ('TPL-005', 1, null, 'active', 'guidance', 'Current proposal-guidance template for full-production scope.', 'commercially_sensitive', null),
    ('TPL-006', 1, null, 'active', 'guidance', 'Current communication-guidance template library. Privacy review remains intentionally separate from this catalogue bootstrap.', 'internal', null),
    ('TPL-007', 1, null, 'active', 'guidance', 'Current combined-file checklist guidance for discovery calls.', 'internal', null),
    ('TPL-008', 1, null, 'active', 'guidance', 'Current combined-file checklist guidance for site visits.', 'internal', null),
    ('TPL-009', 1, null, 'active', 'guidance', 'Current combined-file checklist guidance for event handover.', 'internal', null),
    ('TPL-010', 1, null, 'active', 'guidance', 'Current combined-file checklist guidance for final readiness.', 'internal', null),
    ('TPL-013', 1, null, 'active', 'guidance', 'Current close-out checklist guidance.', 'internal', null)
)
insert into public.knowledge_document_versions (
  document_id,
  version_number,
  source_version_label,
  governance_status,
  authority_classification,
  lifecycle_note,
  confidentiality_level_id,
  version_owner_role
)
select
  kd.id,
  vs.version_number,
  vs.source_version_label,
  vs.governance_status,
  vs.authority_classification,
  vs.lifecycle_note,
  kcl.id,
  vs.version_owner_role
from version_seed vs
join public.knowledge_documents kd
  on kd.document_code = vs.document_code
join public.knowledge_confidentiality_levels kcl
  on kcl.level_code = vs.confidentiality_code
on conflict (document_id, version_number) do update
set
  source_version_label = excluded.source_version_label,
  governance_status = excluded.governance_status,
  authority_classification = excluded.authority_classification,
  lifecycle_note = excluded.lifecycle_note,
  confidentiality_level_id = excluded.confidentiality_level_id,
  version_owner_role = excluded.version_owner_role,
  effective_from = null,
  effective_until = null,
  supersedes_version_id = null,
  approved_at = null,
  approval_notes = null,
  last_reviewed_at = null,
  last_review_notes = null;

with manual_source_seed (
  manual_reference_key,
  source_registry_code,
  original_filename,
  mime_type,
  file_size_bytes,
  checksum_sha256,
  personal_information_status,
  personal_information_notes
) as (
  values
    (
      'CF-001_EDITABLE_MASTER_NOT_PRESENT_LOCALLY',
      null::text,
      null::text,
      null::text,
      null::bigint,
      null::text,
      'unknown',
      'Current editable master is referenced in the approved corpus matrix but is not physically available in the repository.'
    )
)
insert into public.knowledge_source_objects (
  source_registry_id,
  origin_type,
  manual_reference_key,
  original_filename,
  mime_type,
  file_size_bytes,
  checksum_sha256,
  personal_information_status,
  personal_information_notes
)
select
  sr.id,
  'manual_reference',
  mss.manual_reference_key,
  mss.original_filename,
  mss.mime_type,
  mss.file_size_bytes,
  mss.checksum_sha256,
  mss.personal_information_status,
  mss.personal_information_notes
from manual_source_seed mss
left join public.source_registry sr
  on sr.source_code = mss.source_registry_code
on conflict (manual_reference_key) where (origin_type = 'manual_reference') do update
set
  source_registry_id = excluded.source_registry_id,
  original_filename = excluded.original_filename,
  mime_type = excluded.mime_type,
  file_size_bytes = excluded.file_size_bytes,
  checksum_sha256 = excluded.checksum_sha256,
  personal_information_status = excluded.personal_information_status,
  personal_information_notes = excluded.personal_information_notes,
  imported_at = null;

with repository_source_seed (
  source_registry_code,
  repository_relative_path,
  original_filename,
  mime_type,
  file_size_bytes,
  checksum_sha256,
  personal_information_status,
  personal_information_notes
) as (
  values
    ('GOV-001', 'sources/phase-01-03/Knowledge Governance/WNC Rental Knowledge Inventory.xlsm', 'WNC Rental Knowledge Inventory.xlsm', 'application/vnd.ms-excel.sheet.macroenabled.12', 30425, '555be0d23f363faf2095eb10074e24eb5676bdb2b6feb61d5e4111ee43f2db62', 'unknown', null),
    ('GOV-002', 'sources/phase-01-03/Knowledge Governance/WNC Rental Policy Decisions & Change Log.xlsm', 'WNC Rental Policy Decisions & Change Log.xlsm', 'application/vnd.ms-excel.sheet.macroenabled.12', 35223, '32cc06c5a0bfa15720752da6cee97b94e2c12e856474c24fe26ba5756fe3d79f', 'unknown', null),
    ('GOV-003', 'sources/phase-01-03/Knowledge Governance/WNC Rental Data Dictionary.xlsm', 'WNC Rental Data Dictionary.xlsm', 'application/vnd.ms-excel.sheet.macroenabled.12', 70090, '64c5995cc2fe2ea41e5976acc8a7c97e212869678f1ab2030e2a526e5a36855b', 'unknown', null),
    ('CF-002', 'sources/phase-01-03/Client Facing Docs/Updated Rental Lookbook 2026.png', 'Updated Rental Lookbook 2026.png', 'image/png', 728148, '6d144fb9b47e269b347b58cc8f27fa3091319a36ed0e00922d3189ec5a5879a6', 'unknown', null),
    ('CF-003', 'sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions.docx', 'Studio Space _ Terms and Conditions.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 13429, '627b3dcc5de368d2a5342ef4994e6cf48d887f1a1e59d90e0e09f0829e0718bc', 'unknown', null),
    ('CF-004', 'sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions (2).pdf', 'Studio Space _ Terms and Conditions (2).pdf', 'application/pdf', 120845, '69e7ef79d268a71437f5bf66e1aaf73298865eb7638f52a9e3c7f6f93a85da0a', 'unknown', null),
    ('CF-005', 'sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx', 'Full Venue _ Rental Terms and Conditions.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 19473, 'b392d37c13b99bce09768a211a42034180abdd5e9745f1b746d4a1332a858cc9', 'unknown', null),
    ('CF-006', 'sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.pdf', 'Full Venue _ Rental Terms and Conditions.pdf', 'application/pdf', 180226, '8cdf8d2b947d6ebd9a46c48ff0eb3890761185709bae3357dfdfcd377e0b94e0', 'unknown', null),
    ('CF-007', 'sources/phase-01-03/Client Facing Docs/WNC Rental Agreement Template.docx', 'WNC Rental Agreement Template.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 1242827, '84177c2540a458b2758b731c8f87a7222ffb91c4d5231e612bcf9b27dbae6a5c', 'unknown', null),
    ('OPS-001', 'sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx', 'WNC Venue Rental Operations Manual.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 1253923, '0932151ffe7244180cb272682255f4b5fcd4857cf205ffdfa5f3bfd4c4aad6df', 'unknown', null),
    ('OPS-002', 'sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm', 'WNC Venue Technical & Equipment Inventory.xlsm', 'application/vnd.ms-excel.sheet.macroenabled.12', 125591, '94e1053822dbc6adc56b4abadacfd1456cf86b913bfd28fae5ec7b3d94764b63', 'unknown', null),
    ('SERV-001', 'sources/phase-01-03/Catalogues/WNC Rental Services Catalogue.xlsm', 'WNC Rental Services Catalogue.xlsm', 'application/vnd.ms-excel.sheet.macroenabled.12', 17969, 'ffe0ee9e5838e3899a9aa3cbccc5b51d2701de3979647698e957e116018d589d', 'unknown', null),
    ('SERV-003', 'sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm', 'WNC Catering, Beverage & Supplier Catalogue.xlsm', 'application/vnd.ms-excel.sheet.macroenabled.12', 67462, '424610406d34faec3e58fc5d1bfce97bfd4e62e6d8e34b6608c0eb2c322c94a7', 'unknown', null),
    ('HC-AMO-000', 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx', 'WNC Rental Historical Case Library.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 1048346, 'a938439534a2c2c9f34936a28e5d76c59b93117364a3ae2114cf90d9d7b145fd', 'yes', 'Historical reference-only case library containing client-specific operational detail and named individuals in some sections.'),
    ('TPL-001', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Studio Rental Proposal Template.docx', 'Studio Rental Proposal Template.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 10042, 'b5200bccd9c3817c7915da54af5890f5025f5a13f68c1a9468a0ab62ee84e7b5', 'unknown', null),
    ('TPL-002', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Entire Venue Proposal Template.docx', 'Entire Venue Proposal Template.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 10103, 'c1c37608e213eedafaaa60a71413216034f18ed1517a43af05426be14d171976', 'unknown', null),
    ('TPL-003', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Custom Scope Proposal Template.docx', 'Custom Scope Proposal Template.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 10114, '63da5d789803672309af5b5eb67d586f5d780d5b7cf27bb6958fb9ea5134a43e', 'unknown', null),
    ('TPL-004', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Production Coordination Proposal Template.docx', 'Production Coordination Proposal Template.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 10332, 'e75a57e69d751533920a07939bfe3f357254926c32b64a0a563b0d617f3c053b', 'unknown', null),
    ('TPL-005', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Full Production Proposal Template.docx', 'Full Production Proposal Template.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 10319, 'b926e0a9bf0200b298322f1470583598d3c40712f7578ec884b117bde075fe8e', 'unknown', null),
    ('TPL-006', 'sources/phase-01-03/Checklists + Templates/WNC Rental Email Template Library.docx', 'WNC Rental Email Template Library.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 18320, 'ea35bc973b6d4dd0759d1fcb7aa356998a58bbfb55a5f4e3f7bcdca9a7e6ae82', 'unknown', 'May contain privacy-sensitive example patterns in the broader source system, but this repository bootstrap does not assess specific personal-information presence.'),
    ('TPL-007', 'sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx', 'WNC Rental Discovery Call & Site Visit Checklist.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 11064, '9b00e13da8acbb66e1ec25486b3c5185c45244be25f8de7dc4f66b8c23eee085', 'unknown', null),
    ('TPL-009', 'sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx', 'WNC Rental Event Handover & Final Readiness Checklist.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 10256, '224be88d6018225a113e843c02f45b1bc2dbbbca385f0b3d70aeca359b1f297a', 'unknown', null),
    ('TPL-013', 'sources/phase-01-03/Checklists + Templates/WNC Rental Close-Out Checklist.docx', 'WNC Rental Close-Out Checklist.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 8104, '1a5a24fb4b3d3f4f5fc9f01b941a81ed4d862f022f1e3cd322231b717c336f5f', 'unknown', null)
)
insert into public.knowledge_source_objects (
  source_registry_id,
  origin_type,
  repository_relative_path,
  original_filename,
  mime_type,
  file_size_bytes,
  checksum_sha256,
  personal_information_status,
  personal_information_notes
)
select
  sr.id,
  'repository_file',
  rss.repository_relative_path,
  rss.original_filename,
  rss.mime_type,
  rss.file_size_bytes,
  rss.checksum_sha256,
  rss.personal_information_status,
  rss.personal_information_notes
from repository_source_seed rss
left join public.source_registry sr
  on sr.source_code = rss.source_registry_code
on conflict (repository_relative_path) where (origin_type = 'repository_file') do update
set
  source_registry_id = excluded.source_registry_id,
  original_filename = excluded.original_filename,
  mime_type = excluded.mime_type,
  file_size_bytes = excluded.file_size_bytes,
  checksum_sha256 = excluded.checksum_sha256,
  personal_information_status = excluded.personal_information_status,
  personal_information_notes = excluded.personal_information_notes,
  imported_at = null;

with source_relation_seed (
  document_code,
  version_number,
  locator_kind,
  locator_value,
  role_code,
  source_usage_disposition,
  is_preferred_extraction_source,
  is_primary_representation,
  representation_notes
) as (
  values
    ('GOV-001', 1, 'repository_file', 'sources/phase-01-03/Knowledge Governance/WNC Rental Knowledge Inventory.xlsm', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('GOV-002', 1, 'repository_file', 'sources/phase-01-03/Knowledge Governance/WNC Rental Policy Decisions & Change Log.xlsm', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('GOV-003', 1, 'repository_file', 'sources/phase-01-03/Knowledge Governance/WNC Rental Data Dictionary.xlsm', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('CF-001', 1, 'manual_reference', 'CF-001_EDITABLE_MASTER_NOT_PRESENT_LOCALLY', 'authoritative_editable_source', 'excluded_from_extraction', false, false, 'Approved editable master is missing from the repository and is retained only as a manual provenance reference in this bootstrap.'),
    ('CF-001', 1, 'repository_file', 'sources/phase-01-03/Client Facing Docs/Updated Rental Lookbook 2026.png', 'export', 'eligible_for_extraction', true, true, 'Current locally available export representation. Inventory wording says PDF, while the supplied repository artifact is PNG.'),
    ('CF-003', 1, 'repository_file', 'sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('CF-003', 1, 'repository_file', 'sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions (2).pdf', 'export', 'excluded_from_extraction', false, false, 'Older drifted export retained only for provenance and wording-drift review.'),
    ('CF-005', 1, 'repository_file', 'sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('CF-005', 1, 'repository_file', 'sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.pdf', 'export', 'excluded_from_extraction', false, false, 'Older drifted export retained only for provenance and wording-drift review.'),
    ('CF-007', 1, 'repository_file', 'sources/phase-01-03/Client Facing Docs/WNC Rental Agreement Template.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('OPS-001', 1, 'repository_file', 'sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('OPS-002', 1, 'repository_file', 'sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm', 'authoritative_editable_source', 'eligible_for_extraction', true, true, 'Shared current workbook also contains the embedded OPS-003 logical document.'),
    ('OPS-003', 1, 'repository_file', 'sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm', 'supporting_source', 'eligible_for_extraction', true, true, 'Embedded governed subdocument extracted from the shared OPS-002 workbook.'),
    ('SERV-001', 1, 'repository_file', 'sources/phase-01-03/Catalogues/WNC Rental Services Catalogue.xlsm', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('SERV-003', 1, 'repository_file', 'sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm', 'authoritative_editable_source', 'eligible_for_extraction', true, true, 'Shared current workbook also contains the embedded SERV-004 logical document.'),
    ('SERV-004', 1, 'repository_file', 'sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm', 'supporting_source', 'eligible_for_extraction', true, true, 'Embedded governed subdocument extracted from the shared SERV-003 workbook.'),
    ('TPL-001', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Studio Rental Proposal Template.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('TPL-002', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Entire Venue Proposal Template.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('TPL-003', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Custom Scope Proposal Template.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('TPL-004', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Production Coordination Proposal Template.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('TPL-005', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/Proposal Templates/Full Production Proposal Template.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('TPL-006', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/WNC Rental Email Template Library.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null),
    ('TPL-007', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, 'Combined source file also carries the TPL-008 logical document.'),
    ('TPL-008', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx', 'supporting_source', 'eligible_for_extraction', true, true, 'Combined logical document carried inside the shared TPL-007 source file.'),
    ('TPL-009', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, 'Combined source file also carries the TPL-010 logical document.'),
    ('TPL-010', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx', 'supporting_source', 'eligible_for_extraction', true, true, 'Combined logical document carried inside the shared TPL-009 source file.'),
    ('TPL-013', 1, 'repository_file', 'sources/phase-01-03/Checklists + Templates/WNC Rental Close-Out Checklist.docx', 'authoritative_editable_source', 'eligible_for_extraction', true, true, null)
),
resolved_source_objects as (
  select
    'manual_reference'::text as locator_kind,
    manual_reference_key as locator_value,
    id as source_object_id
  from public.knowledge_source_objects
  where manual_reference_key is not null

  union all

  select
    'repository_file'::text as locator_kind,
    repository_relative_path as locator_value,
    id as source_object_id
  from public.knowledge_source_objects
  where repository_relative_path is not null
)
insert into public.knowledge_document_version_source_objects (
  document_version_id,
  source_object_id,
  source_object_role_id,
  source_usage_disposition,
  is_preferred_extraction_source,
  is_primary_representation,
  representation_notes
)
select
  kdv.id,
  rso.source_object_id,
  ksor.id,
  srs.source_usage_disposition,
  srs.is_preferred_extraction_source,
  srs.is_primary_representation,
  srs.representation_notes
from source_relation_seed srs
join public.knowledge_documents kd
  on kd.document_code = srs.document_code
join public.knowledge_document_versions kdv
  on kdv.document_id = kd.id
 and kdv.version_number = srs.version_number
join resolved_source_objects rso
  on rso.locator_kind = srs.locator_kind
 and rso.locator_value = srs.locator_value
join public.knowledge_source_object_roles ksor
  on ksor.role_code = srs.role_code
on conflict (document_version_id, source_object_id, source_object_role_id) do update
set
  source_usage_disposition = excluded.source_usage_disposition,
  is_preferred_extraction_source = excluded.is_preferred_extraction_source,
  is_primary_representation = excluded.is_primary_representation,
  representation_notes = excluded.representation_notes;

with audience_seed (
  document_code,
  version_number,
  audience_code
) as (
  values
    ('GOV-001', 1, 'knowledge_owner'),
    ('GOV-001', 1, 'rental_coordinator'),
    ('GOV-002', 1, 'knowledge_owner'),
    ('GOV-002', 1, 'general_manager'),
    ('GOV-002', 1, 'rental_coordinator'),
    ('GOV-003', 1, 'knowledge_owner'),
    ('GOV-003', 1, 'rental_coordinator'),
    ('CF-001', 1, 'prospective_client'),
    ('CF-001', 1, 'rental_coordinator'),
    ('CF-001', 1, 'marketing_brand'),
    ('CF-003', 1, 'confirmed_client'),
    ('CF-003', 1, 'rental_coordinator'),
    ('CF-003', 1, 'general_manager'),
    ('CF-003', 1, 'client_facing_staff'),
    ('CF-005', 1, 'confirmed_client'),
    ('CF-005', 1, 'rental_coordinator'),
    ('CF-005', 1, 'general_manager'),
    ('CF-005', 1, 'client_facing_staff'),
    ('CF-007', 1, 'confirmed_client'),
    ('CF-007', 1, 'rental_coordinator'),
    ('CF-007', 1, 'general_manager'),
    ('CF-007', 1, 'operations'),
    ('OPS-001', 1, 'operations'),
    ('OPS-001', 1, 'rental_coordinator'),
    ('OPS-001', 1, 'general_manager'),
    ('OPS-001', 1, 'event_lead'),
    ('OPS-002', 1, 'operations'),
    ('OPS-002', 1, 'facilities'),
    ('OPS-002', 1, 'rental_coordinator'),
    ('OPS-003', 1, 'operations'),
    ('OPS-003', 1, 'general_manager'),
    ('OPS-003', 1, 'rental_coordinator'),
    ('SERV-001', 1, 'rental_coordinator'),
    ('SERV-001', 1, 'operations'),
    ('SERV-001', 1, 'general_manager'),
    ('SERV-003', 1, 'rental_coordinator'),
    ('SERV-003', 1, 'operations'),
    ('SERV-003', 1, 'supplier_coordinator'),
    ('SERV-004', 1, 'operations'),
    ('SERV-004', 1, 'rental_coordinator'),
    ('SERV-004', 1, 'supplier_coordinator'),
    ('TPL-001', 1, 'rental_coordinator'),
    ('TPL-001', 1, 'client_facing_staff'),
    ('TPL-002', 1, 'rental_coordinator'),
    ('TPL-002', 1, 'client_facing_staff'),
    ('TPL-003', 1, 'rental_coordinator'),
    ('TPL-003', 1, 'client_facing_staff'),
    ('TPL-004', 1, 'rental_coordinator'),
    ('TPL-005', 1, 'rental_coordinator'),
    ('TPL-005', 1, 'general_manager'),
    ('TPL-006', 1, 'rental_coordinator'),
    ('TPL-006', 1, 'client_facing_staff'),
    ('TPL-007', 1, 'rental_coordinator'),
    ('TPL-007', 1, 'client_facing_staff'),
    ('TPL-008', 1, 'rental_coordinator'),
    ('TPL-008', 1, 'operations'),
    ('TPL-009', 1, 'rental_coordinator'),
    ('TPL-009', 1, 'operations'),
    ('TPL-009', 1, 'event_lead'),
    ('TPL-010', 1, 'operations'),
    ('TPL-010', 1, 'event_lead'),
    ('TPL-013', 1, 'rental_coordinator'),
    ('TPL-013', 1, 'finance'),
    ('TPL-013', 1, 'operations')
)
insert into public.knowledge_document_version_audiences (
  document_version_id,
  audience_id
)
select
  kdv.id,
  ka.id
from audience_seed ads
join public.knowledge_documents kd
  on kd.document_code = ads.document_code
join public.knowledge_document_versions kdv
  on kdv.document_id = kd.id
 and kdv.version_number = ads.version_number
join public.knowledge_audiences ka
  on ka.audience_code = ads.audience_code
on conflict (document_version_id, audience_id) do nothing;

with rental_type_seed (
  document_code,
  version_number,
  rental_type_code
) as (
  values
    ('GOV-001', 1, 'studio_space'),
    ('GOV-001', 1, 'entire_venue'),
    ('GOV-001', 1, 'custom_scope'),
    ('GOV-002', 1, 'studio_space'),
    ('GOV-002', 1, 'entire_venue'),
    ('GOV-002', 1, 'custom_scope'),
    ('GOV-003', 1, 'studio_space'),
    ('GOV-003', 1, 'entire_venue'),
    ('GOV-003', 1, 'custom_scope'),
    ('CF-001', 1, 'studio_space'),
    ('CF-001', 1, 'entire_venue'),
    ('CF-001', 1, 'custom_scope'),
    ('CF-003', 1, 'studio_space'),
    ('CF-005', 1, 'entire_venue'),
    ('CF-007', 1, 'studio_space'),
    ('CF-007', 1, 'entire_venue'),
    ('CF-007', 1, 'custom_scope'),
    ('OPS-001', 1, 'studio_space'),
    ('OPS-001', 1, 'entire_venue'),
    ('OPS-001', 1, 'custom_scope'),
    ('OPS-002', 1, 'studio_space'),
    ('OPS-002', 1, 'entire_venue'),
    ('OPS-002', 1, 'custom_scope'),
    ('OPS-003', 1, 'studio_space'),
    ('OPS-003', 1, 'entire_venue'),
    ('OPS-003', 1, 'custom_scope'),
    ('SERV-001', 1, 'studio_space'),
    ('SERV-001', 1, 'entire_venue'),
    ('SERV-001', 1, 'custom_scope'),
    ('SERV-003', 1, 'studio_space'),
    ('SERV-003', 1, 'entire_venue'),
    ('SERV-003', 1, 'custom_scope'),
    ('SERV-004', 1, 'studio_space'),
    ('SERV-004', 1, 'entire_venue'),
    ('SERV-004', 1, 'custom_scope'),
    ('TPL-001', 1, 'studio_space'),
    ('TPL-002', 1, 'entire_venue'),
    ('TPL-003', 1, 'custom_scope'),
    ('TPL-006', 1, 'studio_space'),
    ('TPL-006', 1, 'entire_venue'),
    ('TPL-006', 1, 'custom_scope'),
    ('TPL-007', 1, 'studio_space'),
    ('TPL-007', 1, 'entire_venue'),
    ('TPL-007', 1, 'custom_scope'),
    ('TPL-008', 1, 'studio_space'),
    ('TPL-008', 1, 'entire_venue'),
    ('TPL-008', 1, 'custom_scope'),
    ('TPL-009', 1, 'studio_space'),
    ('TPL-009', 1, 'entire_venue'),
    ('TPL-009', 1, 'custom_scope'),
    ('TPL-010', 1, 'studio_space'),
    ('TPL-010', 1, 'entire_venue'),
    ('TPL-010', 1, 'custom_scope'),
    ('TPL-013', 1, 'studio_space'),
    ('TPL-013', 1, 'entire_venue'),
    ('TPL-013', 1, 'custom_scope')
)
insert into public.knowledge_document_version_rental_types (
  document_version_id,
  rental_type_id
)
select
  kdv.id,
  rt.id
from rental_type_seed rts
join public.knowledge_documents kd
  on kd.document_code = rts.document_code
join public.knowledge_document_versions kdv
  on kdv.document_id = kd.id
 and kdv.version_number = rts.version_number
join public.rental_types rt
  on rt.rental_type_code = rts.rental_type_code
on conflict (document_version_id, rental_type_id) do nothing;

with logical_rule_seed (
  document_code,
  version_number,
  rule_code,
  relationship_type_code,
  notes
) as (
  values
    ('CF-003', 1, 'EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'governed_by', 'Studio terms contain controlled wording about the expedited surcharge trigger and treatment.'),
    ('CF-003', 1, 'OPER_STUDIO_GRACE_PERIOD', 'governed_by', 'Studio terms contain controlled wording about the 15 minute arrival and departure grace period.'),
    ('CF-003', 1, 'CATER_VAT_COORDINATION_SERVICE_21_PERCENT', 'governed_by', 'Studio terms contain controlled wording about catering coordination VAT treatment.'),
    ('CF-005', 1, 'EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'governed_by', 'Full Venue terms contain controlled wording about the expedited surcharge trigger and treatment.'),
    ('CF-005', 1, 'CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'governed_by', 'Full Venue terms reference the whole-venue legal maximum as contextual controlled knowledge.'),
    ('CF-005', 1, 'OPER_ENTIRE_VENUE_GRACE_PERIOD', 'governed_by', 'Full Venue terms contain controlled wording about the 30 minute arrival and departure grace period.'),
    ('CF-007', 1, 'PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT', 'governed_by', 'Agreement template captures the confirmation-threshold rule inside the confirmed scope wording.'),
    ('CF-007', 1, 'EXPEDITED_SURCHARGE_WITHIN_14_DAYS', 'governed_by', 'Agreement template captures the expedited surcharge or waiver in confirmed booking scope.'),
    ('OPS-001', 1, 'OPER_STUDIO_GRACE_PERIOD', 'operational_context_for', 'Operations Manual provides the controlled procedure context around the Studio grace-period rule.'),
    ('OPS-001', 1, 'OPER_ENTIRE_VENUE_GRACE_PERIOD', 'operational_context_for', 'Operations Manual provides the controlled procedure context around the Entire Venue grace-period rule.'),
    ('OPS-001', 1, 'OPER_SETUP_START_AT_BOOKED_TIME', 'operational_context_for', 'Operations Manual provides the operational procedure context for booked-time setup boundaries.'),
    ('OPS-001', 1, 'OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL', 'operational_context_for', 'Operations Manual provides the operational procedure context for early-access approvals.'),
    ('OPS-001', 1, 'OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY', 'operational_context_for', 'Operations Manual provides the operational procedure context for supplier access being limited to approved times.'),
    ('OPS-001', 1, 'OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', 'operational_context_for', 'Operations Manual provides the operational procedure context for professional-cleaning review.'),
    ('OPS-002', 1, 'CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'governed_by', 'Technical inventory workbook contains the current governed whole-venue legal maximum source material.'),
    ('OPS-002', 1, 'ACCESS_STUDIO_RETAIL_SHARED', 'governed_by', 'Technical inventory workbook contains the current governed shared-retail access material for Studio rentals.'),
    ('OPS-002', 1, 'ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'governed_by', 'Technical inventory workbook contains the current governed one-to-one-room inclusion material for Entire Venue rentals.'),
    ('OPS-002', 1, 'TECH_WIFI_STANDARD', 'governed_by', 'Technical inventory workbook contains the current governed standard Wi-Fi capability material.'),
    ('OPS-002', 1, 'TECH_BASIC_PROJECTOR_REQUEST_ONLY', 'governed_by', 'Technical inventory workbook contains the current governed projector-on-request capability material.'),
    ('OPS-002', 1, 'TECH_REQ_CUSTOM_TECH_CONFIRM', 'governed_by', 'Technical inventory workbook contains the current governed custom-technical-review requirement material.'),
    ('OPS-003', 1, 'CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM', 'governed_by', 'Embedded capacity-and-space-use source directly concerns the governed whole-venue legal maximum rule.'),
    ('OPS-003', 1, 'CAPACITY_STUDIO_LYING_DOWN', 'governed_by', 'Embedded capacity-and-space-use source directly concerns the governed Studio lying-down capacity rule.'),
    ('OPS-003', 1, 'CAPACITY_RETAIL_STANDING', 'governed_by', 'Embedded capacity-and-space-use source directly concerns the governed Retail standing-capacity rule.'),
    ('SERV-001', 1, 'SERVICE_LEVEL_VENUE_ONLY', 'governed_by', 'Services catalogue directly concerns the governed Venue Only service-level rule.'),
    ('SERV-001', 1, 'SERVICE_LEVEL_SUPPORTED_RENTAL', 'governed_by', 'Services catalogue directly concerns the governed Supported Rental service-level rule.'),
    ('SERV-001', 1, 'SERVICE_LEVEL_FULL_PRODUCTION', 'governed_by', 'Services catalogue directly concerns the governed Full Production service-level rule.'),
    ('SERV-001', 1, 'SERVICE_ITEM_EVENT_MANAGER', 'governed_by', 'Services catalogue directly concerns the governed Event Manager service-item rule.'),
    ('SERV-001', 1, 'SERVICE_ITEM_FACILITATOR_SOURCING', 'governed_by', 'Services catalogue directly concerns the governed Facilitator Sourcing service-item rule.'),
    ('SERV-001', 1, 'FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED', 'governed_by', 'Services catalogue directly concerns the governed WNC-provided facilitator confirmation rule.'),
    ('SERV-003', 1, 'CATER_EXTERNAL_CATERER_ALLOWED', 'governed_by', 'Catering catalogue directly concerns the governed external-caterer allowance rule.'),
    ('SERV-003', 1, 'CATER_WNC_PARTNER_AVAILABLE', 'governed_by', 'Catering catalogue directly concerns the governed WNC catering-partner availability rule.'),
    ('SERV-003', 1, 'CATER_VAT_PRODUCTS_9_PERCENT', 'governed_by', 'Catering catalogue directly concerns the governed catering-product VAT rule.'),
    ('SERV-003', 1, 'CATER_VAT_COORDINATION_SERVICE_21_PERCENT', 'governed_by', 'Catering catalogue directly concerns the governed coordination-service VAT rule.'),
    ('SERV-003', 1, 'CATER_VAT_MIXED_SPLIT_REQUIRED', 'governed_by', 'Catering catalogue directly concerns the governed mixed-VAT split rule.'),
    ('SERV-004', 1, 'CATER_EXTERNAL_CATERER_STORAGE_CONFIRM', 'operational_context_for', 'Embedded supplier-requirements source provides the operational context for caterer storage confirmation.'),
    ('SERV-004', 1, 'CATER_EXTERNAL_BARISTA_POWER_CONFIRM', 'operational_context_for', 'Embedded supplier-requirements source provides the operational context for barista-machine power confirmation.'),
    ('SERV-004', 1, 'CATER_EXTERNAL_BARISTA_STORAGE_CONFIRM', 'operational_context_for', 'Embedded supplier-requirements source provides the operational context for barista storage confirmation.'),
    ('TPL-004', 1, 'SERVICE_ITEM_PRODUCTION_COORDINATION', 'operational_context_for', 'Production-coordination proposal template provides current scope wording around the production-coordination service item.'),
    ('TPL-004', 1, 'SERVICE_ITEM_TECHNICAL_COORDINATION', 'operational_context_for', 'Production-coordination proposal template provides current scope wording around the technical-coordination service item.'),
    ('TPL-005', 1, 'SERVICE_LEVEL_FULL_PRODUCTION', 'operational_context_for', 'Full-production proposal template provides current scope wording around the Full Production service level.'),
    ('TPL-005', 1, 'SERVICE_ITEM_EVENT_MANAGER', 'operational_context_for', 'Full-production proposal template provides current scope wording around the Event Manager service item.'),
    ('TPL-005', 1, 'SERVICE_ITEM_PRODUCTION_COORDINATION', 'operational_context_for', 'Full-production proposal template provides current scope wording around the Production Coordination service item.')
)
insert into public.knowledge_document_version_logical_rules (
  document_version_id,
  rule_code,
  relationship_type_id,
  notes
)
select
  kdv.id,
  lrs.rule_code,
  krrt.id,
  lrs.notes
from logical_rule_seed lrs
join public.knowledge_documents kd
  on kd.document_code = lrs.document_code
join public.knowledge_document_versions kdv
  on kdv.document_id = kd.id
 and kdv.version_number = lrs.version_number
join public.knowledge_rule_relationship_types krrt
  on krrt.relationship_type_code = lrs.relationship_type_code
on conflict (document_version_id, rule_code, relationship_type_id) do update
set
  notes = excluded.notes;

with historical_case_seed (
  case_code,
  canonical_title
) as (
  values
    ('HC-001', 'Merrachi Multi-Day Retail Pop-Up'),
    ('HC-002', 'Philips Coffee Machine Showcase'),
    ('HC-003', 'WineGB Trade & Press Showcase'),
    ('HC-004', 'Amoué PR Wellness Event'),
    ('HC-005', 'British Embassy / GreenTech Corporate Reception'),
    ('HC-006', 'Sheso Trading Event'),
    ('HC-007', 'MOOI / Little Wonderland PR Activation'),
    ('HC-008', 'Vanessa Corporate Wellness Outing / Lululemon Branding Requirement'),
    ('HC-009', 'ADE Event Permit, Alcohol, Sound & Operational Compliance Precedent')
)
insert into public.historical_cases (
  case_code,
  canonical_title
)
select
  hcs.case_code,
  hcs.canonical_title
from historical_case_seed hcs
on conflict (case_code) do update
set canonical_title = excluded.canonical_title;

with historical_case_seed (
  case_code
) as (
  values
    ('HC-001'),
    ('HC-002'),
    ('HC-003'),
    ('HC-004'),
    ('HC-005'),
    ('HC-006'),
    ('HC-007'),
    ('HC-008'),
    ('HC-009')
),
alias_seed (
  case_code,
  alias_text,
  alias_type
) as (
  values
    ('HC-005', 'British Embassy', 'client'),
    ('HC-005', 'GreenTech', 'shorthand'),
    ('HC-007', 'MOOI', 'brand'),
    ('HC-007', 'Little Wonderland', 'brand'),
    ('HC-008', 'Vanessa', 'person'),
    ('HC-008', 'Lululemon', 'brand')
),
resolved_alias_seed as (
  select
    hc.id as historical_case_id,
    als.alias_text,
    als.alias_type
  from alias_seed als
  join public.historical_cases hc
    on hc.case_code = als.case_code
)
delete from public.historical_case_aliases hca
using public.historical_cases hc
join historical_case_seed hcs
  on hcs.case_code = hc.case_code
where hca.historical_case_id = hc.id
  and not exists (
    select 1
    from resolved_alias_seed ras
    where ras.historical_case_id = hca.historical_case_id
      and private.normalize_historical_case_alias_text(ras.alias_text) = private.normalize_historical_case_alias_text(hca.alias_text)
  );

with alias_seed (
  case_code,
  alias_text,
  alias_type
) as (
  values
    ('HC-005', 'British Embassy', 'client'),
    ('HC-005', 'GreenTech', 'shorthand'),
    ('HC-007', 'MOOI', 'brand'),
    ('HC-007', 'Little Wonderland', 'brand'),
    ('HC-008', 'Vanessa', 'person'),
    ('HC-008', 'Lululemon', 'brand')
),
resolved_alias_seed as (
  select
    hc.id as historical_case_id,
    als.alias_text,
    als.alias_type
  from alias_seed als
  join public.historical_cases hc
    on hc.case_code = als.case_code
)
update public.historical_case_aliases hca
set alias_type = ras.alias_type
from resolved_alias_seed ras
where hca.historical_case_id = ras.historical_case_id
  and private.normalize_historical_case_alias_text(hca.alias_text) = private.normalize_historical_case_alias_text(ras.alias_text)
  and hca.alias_type is distinct from ras.alias_type;

with alias_seed (
  case_code,
  alias_text,
  alias_type
) as (
  values
    ('HC-005', 'British Embassy', 'client'),
    ('HC-005', 'GreenTech', 'shorthand'),
    ('HC-007', 'MOOI', 'brand'),
    ('HC-007', 'Little Wonderland', 'brand'),
    ('HC-008', 'Vanessa', 'person'),
    ('HC-008', 'Lululemon', 'brand')
)
insert into public.historical_case_aliases (
  historical_case_id,
  alias_text,
  alias_type
)
select
  hc.id,
  als.alias_text,
  als.alias_type
from alias_seed als
join public.historical_cases hc
  on hc.case_code = als.case_code
where not exists (
  select 1
  from public.historical_case_aliases existing_alias
  where existing_alias.historical_case_id = hc.id
    and private.normalize_historical_case_alias_text(existing_alias.alias_text) = private.normalize_historical_case_alias_text(als.alias_text)
);

with historical_case_version_seed (
  case_code,
  version_number,
  governance_status,
  precedent_availability,
  precedent_type,
  evidence_strength,
  historical_event_status,
  temporal_precision,
  curated_narrative,
  confidentiality_level_code,
  personal_information_status,
  personal_information_notes
) as (
  values
    (
      'HC-001',
      1,
      'draft',
      'active',
      'full_case',
      'strong',
      'completed',
      'unknown',
      $hc001$
Case 01: Merrachi Multi-Day Retail Pop-Up
Rental type: Multi-day entire-venue brand / retail takeover.
Why this case matters
WNC’s clearest example of a true full-venue takeover where the client wanted the venue effectively turned into a white box and then operated independently with its own event, drinks and cleaning teams.
How the rental worked
Merrachi took over the full venue and largely operated independently once the space had been handed over. WNC’s main production responsibility was clearing the venue and preparing it for handover. The client then handled its own event operations, drinks team, cleaning team and event materials.
Responsibility split
WNC
• Full clearing of the agreed venue areas.
• Moving WNC stock, furniture and equipment out of sight.
• Preparing the venue for white-box handover.
• Managing the transition from normal WNC operations into the rental.
Client / production team
• Event operation.
• Own drinks team.
• Own cleaning team.
• Client products and event materials.
• Day-to-day management once the venue was handed over.
What made it complicated
• The main challenge was not operating the event; it was creating a workable moving plan for WNC’s own stock, furniture, kitchen items and back-office contents.
• WNC still needed to remain operational until the evening before the takeover, so the space could not simply be emptied several days in advance.
• Patrick moved stock into external storage progressively.
• Furniture, blankets and meditation cushions were moved into the former Ice Bath / Storage Room.
• Yoga mats were hidden behind the plants.
• Most kitchen items, Back Office contents and stock were moved to external storage.
• Some operational stock had to remain available until shortly before final handover.
Key lessons
• Large multi-day takeovers need a venue-clearing and moving plan, not simply a note saying the venue will be cleared.
• Determine early what needs to leave the building, what can remain hidden onsite and what must stay operational until the final evening.
• External storage may be necessary when WNC’s own Storage Room is insufficient.
• Account for the labour and timing required to move WNC’s normal operating environment out of the space.
• Plan the final clearing sequence around the last normal WNC operating day.
• Once a true full takeover has been handed over, WNC does not necessarily need to remain operationally involved if the client has brought its own teams.
Useful precedent for
Multi-day takeovers, white-box activations, large brand pop-ups, rentals requiring complete venue clearing and events requiring significant offsite storage.
$hc001$,
      'restricted',
      'yes',
      'Curated narrative preserves named-individual operational detail from the historical case library.'
    ),
    (
      'HC-002',
      1,
      'draft',
      'active',
      'full_case',
      'strong',
      'completed',
      'unknown',
      $hc002$
Case 02: Philips Coffee Machine Showcase
Rental type: Brand activation / product showcase with significant technical and catering requirements.
Why this case matters
This case exposed two important operational issues: electrical load from production equipment and cleaning requirements for high-footfall events with full catering.
How the rental worked
The client brought a substantial production setup for a coffee-machine showcase, including many machines running simultaneously. WNC handled the cleaning. The client also requested physical changes to the venue, including removal of the large decorative rocks, which had to be moved into the courtyard several days before the event.
Responsibility split
WNC
• Venue preparation.
• Agreed venue clearing.
• Cleaning.
• Removing agreed WNC venue elements such as the rocks.
• Venue-side operational coordination.
Client / production team
• Product showcase.
• Coffee machines and production equipment.
• Technical production requirements.
• Production team and suppliers.
What made it complicated
• A large number of machines needed to run at the same time, creating much more electrical demand than a standard rental.
• The production setup was complex enough that WNC should not be expected to independently validate the full electrical load.
• The rocks had to be removed days before the event and stored in the courtyard.
• High foot traffic plus a full catering team created substantially more mess than expected.
Key lessons
• Collect power requirements per machine or equipment item early for equipment-heavy productions.
• For substantial electrical loads, recommend that the client’s production team brings a qualified electrician or technical professional to assess the setup and distribution requirements.
• Do not assume that knowing the venue’s available circuits is enough for a complex production.
• Major physical venue changes need lead time.
• High-volume events with significant catering can create far more cleaning than a normal rental.
• Professional cleaning should be required or strongly recommended for high-impact, high-footfall rentals with substantial catering or production.
• The coffee machine can fit inside the ice-bath in the storage room, as we had to remove it out of they way.
Useful precedent for
Product showcases, equipment-heavy activations, coffee or food activations, events with substantial power requirements and high-footfall catered events.
$hc002$,
      'commercially_sensitive',
      'no',
      null
    ),
    (
      'HC-003',
      1,
      'draft',
      'limited',
      'full_case',
      'strong',
      'completed',
      'unknown',
      $hc003$
Case 03: WineGB Trade & Press Showcase
Rental type: Trade / press showcase with significant WNC production support.
Why this case matters
A strong example of WNC providing real production support while maintaining a clear boundary between production/venue support and running the client’s guest-facing event.
How the rental worked
WNC helped prepare and physically set up the venue according to the agreed production scope. The client also had a substantial quantity of wine that needed to be delivered before the event. WNC’s own storage was not sufficient, so the larger external bike-storage / hallway storage space was hired for €300 for the day.
Responsibility split
WNC
• Venue preparation and agreed production setup.
• Furniture / equipment coordination where included.
• Supplier and delivery coordination.
• Storage coordination.
• Venue cleanliness and operational support.
• Floral arrangements where included; Haylin can handle floral arrangements.
Client / production team
• Running the trade showcase.
• Hosting attendees.
• Exhibitor activity.
• Guest-facing event operation.
External suppliers / facilitators
• Catering and hired production items as applicable.
What made it complicated
• Multiple suppliers and deliveries.
• Production setup by WNC.
• Large volume of wine requiring advance delivery.
• Insufficient normal venue storage.
• Furniture and equipment availability.
• Procurement timing.
Key lessons
• Production coordination can include physically setting up the venue to the agreed scope, not merely emailing suppliers.
• Agree delivery dates and storage requirements before products arrive.
• Large-volume deliveries may require the additional external storage space.
• Always ask the client how much needs to be stored, not simply whether they require storage.
• Production items should be booked or purchased in good time because items can go out of stock if sourcing is left too late.
• WNC onsite staff can provide production and venue support without becoming event hosts, servers or exhibitor assistants.
• Haylin can provide floral arrangement support where appropriate.
Useful precedent for
Trade events, showcases, corporate receptions, events involving advance deliveries and storage, and rentals where WNC is providing production support.
$hc003$,
      'restricted',
      'yes',
      'Curated narrative preserves named-individual capability detail from the historical case library.'
    ),
    (
      'HC-004',
      1,
      'draft',
      'limited',
      'full_case',
      'strong',
      'completed',
      'unknown',
      $hc004$
Case 04: Amoué PR Wellness Event
Rental type: Beauty / PR brand event with wellness programming.
Why this case matters
This event produced two especially useful lessons: catering needs to fit the sensory context of the event, and an upcoming brand asking for exposure-based or gift-based pricing is not automatically a strategic collaboration.
How the rental worked
The event combined a PR / beauty activation with several wellness sessions. WNC did not handle the catering. The 1:1 / Podcast Room was also used as practical overflow for bags and event storage.
What made it complicated
• Food brought into the venue had a strong smell.
• For perfume, beauty, skincare or other sensory PR events, strong food smells can interfere with the intended guest and product experience.
• The brand also tried to negotiate a lower venue rate because they were an upcoming brand, including offering staff gifts / a Christmas basket as part of the value exchange.
Catering context lesson
For PR and sensory brand events, WNC should consider not only whether food can physically be served in the venue, but whether the smell and style of the catering makes sense for the experience. Strong-smelling food should generally be avoided for perfume, fragrance, beauty, skincare and other scent-sensitive activations. This is not a blanket rule for food-focused or gut-health events.
Discount / collaboration lesson
Being an upcoming brand, offering exposure or providing gifts is not on its own a reason to discount the rental. Reduced or collaboration pricing should only be considered where WNC identifies a genuine strategic benefit, such as strong audience alignment, a meaningful partnership opportunity, a launch with a major wellness creator, or another clearly reciprocal collaboration.
Key lessons
• Match catering style and smell to the event experience.
• Avoid strong-smelling foods for scent-sensitive PR and beauty events.
• Do not discount simply because a brand is new, offers exposure or offers staff gifts.
• Collaboration pricing should have a clear strategic reason for WNC.
Useful precedent for
Beauty, perfume and skincare PR; sensory activations; catering decisions based on event context; and requests for discounted rental rates or collaborations.
$hc004$,
      'restricted',
      'no',
      null
    ),
    (
      'HC-005',
      1,
      'draft',
      'active',
      'full_case',
      'strong',
      'completed',
      'unknown',
      $hc005$
Case 05: British Embassy / GreenTech Corporate Reception
Rental type: Corporate networking / reception.
Why this case matters
A useful example of a more traditional corporate event using WNC rather than a wellness-led rental.
How the rental worked
The event involved standing reception use, catering coordination, drinks, furniture requirements and audiovisual needs. The client brought wine, while venue/service requirements such as glassware, standing tables and projector/AV were part of the planning discussion.
Responsibility split
WNC
• Venue.
• Agreed catering / supplier coordination.
• Agreed equipment and venue support.
• Operational guidance.
Client / production team
• Corporate event content.
• Guests.
• Client-provided wine.
• Client-specific event requirements.
What made it complicated
• Alcohol arrangements.
• Catering responsibilities.
• Equipment and furniture requirements.
• Technical setup.
• Clear division between client-provided and WNC-provided elements.
Key lessons
• Drinks arrangements need to identify exactly who supplies and who serves.
• Technical requirements should be identified before the final event handover.
• Corporate receptions can use the venue successfully without wellness programming.
• Responsibility boundaries matter even for relatively straightforward events.
Useful precedent for
Networking receptions, embassy / corporate events, standing events and client-provided beverage arrangements.
$hc005$,
      'commercially_sensitive',
      'no',
      null
    ),
    (
      'HC-006',
      1,
      'draft',
      'active',
      'full_case',
      'strong',
      'completed',
      'unknown',
      $hc006$
Case 06: Sheso Trading Event
Rental type: PR / industry event with high guest turnover, client team, external catering and wellness elements.
Why this case matters
This case exposed practical problems around storage planning and build-up overtime for a busy one-day rental.
How the rental worked
This was primarily a one-day event rather than a multi-day white-box takeover. The client wanted to use much of WNC’s existing furniture and venue character, so the entire venue was not emptied in the same way as Merrachi. However, the client brought a significant amount of event material and there was not enough storage available on the day.
What made it complicated
• Not enough storage had been planned for the amount of event material arriving onsite.
• For full-venue brand activations, visible WNC retail stock still usually needs to be cleared even when the client wants to keep WNC’s furniture.
• The client continued build-up later than the agreed time the evening before the event, requiring WNC staff to stay onsite beyond the agreed hours.
Storage planning
For one-day rentals where WNC does not fully clear the venue, confirm approximately how much event material the client needs to store onsite. Possible storage options include the 1:1 / Podcast Room, Back Office, WNC Storage Room and additional external storage where required.
Build-up overtime
Build-up hours need a firm end time. If client build-up runs beyond the agreed access period, additional WNC staffing / overtime applies. The onsite team should not be expected to stay indefinitely because the client’s production is running late.
Key lessons
• Ask for approximate storage volume, not merely whether storage is required.
• For many one-day activations, clients want WNC furniture but not visible WNC retail stock.
• Create a clear storage destination for anything that has to be cleared.
• Build-up hours need a firm end time.
• If build-up runs late, additional WNC staff time and the applicable rental overtime charge should be applied.
Useful precedent for
One-day PR events, high-turnover activations, rentals requiring moderate venue clearing and events with evening-before build-up.
$hc006$,
      'restricted',
      'no',
      null
    ),
    (
      'HC-007',
      1,
      'draft',
      'active',
      'full_case',
      'strong',
      'completed',
      'unknown',
      $hc007$
Case 07: MOOI / Little Wonderland PR Activation
Rental type: Whole-venue PR / beauty activation.
Why this case matters
A useful precedent for grace-period boundaries, early setup and prohibited production materials.
How the rental worked
The client had a 30-minute pre-rental grace period for arrival but began actively setting up during that period. The event also used fake snow as part of the activation. The material caused cleanup problems and damaged / broke WNC’s vacuum cleaner.
What made it complicated
• The distinction between arrival time and paid build-up time was not enforced clearly enough.
• Fake snow created unusual residue and caused actual equipment damage.
Grace period lesson
The 30-minute entire-venue grace period is for arrival, traffic allowance, entering the building and preparing to begin at the agreed rental time. It is not free build-up time. Operational setup begins at the contracted rental / build-up start time.
Production materials lesson
Fake snow is not permitted. Other unusual materials that create residue, particles, staining, difficult cleanup or potential damage should be discussed before use.
Key lessons
• Grace period does not equal setup time.
• If a client needs additional production time, include it in the agreed schedule.
• Fake snow is prohibited.
• Be explicit with PR and production agencies about arrival versus setup, build-up start/end times, overtime, unusual production materials, clearing and reset responsibilities.
Useful precedent for
PR activations, beauty launches, production-heavy one-day events, unusual styling materials and enforcing build-up / access boundaries.
$hc007$,
      'restricted',
      'no',
      null
    ),
    (
      'HC-008',
      1,
      'draft',
      'limited',
      'limited_precedent',
      'limited',
      'completed',
      'unknown',
      $hc008$
Vanessa Corporate Wellness Outing / Lululemon Branding Requirement
Small corporate wellness rental for approximately 12 guests involving breathwork and cacao. The rental interacted with WNC’s existing class schedule and also included a branding requirement: competing Alo Yoga branding should not be visible. WNC confirmed that unbranded equipment could be used.
Lesson: Ask about competitor-brand restrictions when working with major branded clients. A minor logo or equipment detail can matter significantly to the client.
Useful precedent for: Corporate wellness outings, branded-company events and competitor-brand restrictions.
$hc008$,
      'commercially_sensitive',
      'no',
      null
    ),
    (
      'HC-009',
      1,
      'draft',
      'limited',
      'cautionary_precedent',
      'limited',
      'planning_only',
      'unknown',
      $hc009$
ADE Event: Permit, Alcohol, Sound & Operational Compliance
Planning for an ADE event exposed several issues that had not historically been checked early enough, including alcohol arrangements, amplified sound, fire-safety requirements and relevant municipal / event requirements.
Lesson: Events involving DJs or amplified music, alcohol, unusual guest numbers, exterior/public-space activity or other non-standard use should trigger an early permit and compliance check.
The historical solution used for the ADE event is not a current legal precedent. Current Amsterdam requirements must always be checked for the specific event.
Useful precedent for: ADE events, nightlife-adjacent events, alcohol service, DJs and higher-impact activations.
$hc009$,
      'restricted',
      'no',
      null
    )
)
insert into public.historical_case_versions (
  historical_case_id,
  version_number,
  governance_status,
  precedent_availability,
  precedent_type,
  evidence_strength,
  historical_event_status,
  temporal_precision,
  event_date_start,
  event_date_end,
  temporal_note,
  curated_narrative,
  confidentiality_level_id,
  personal_information_status,
  personal_information_notes,
  contains_historical_value_only_content,
  supersedes_version_id,
  activated_at
)
select
  hc.id,
  hcvs.version_number,
  hcvs.governance_status,
  hcvs.precedent_availability,
  hcvs.precedent_type,
  hcvs.evidence_strength,
  hcvs.historical_event_status,
  hcvs.temporal_precision,
  null,
  null,
  null,
  hcvs.curated_narrative,
  kcl.id,
  hcvs.personal_information_status,
  hcvs.personal_information_notes,
  false,
  null,
  null
from historical_case_version_seed hcvs
join public.historical_cases hc
  on hc.case_code = hcvs.case_code
join public.knowledge_confidentiality_levels kcl
  on kcl.level_code = hcvs.confidentiality_level_code
on conflict (historical_case_id, version_number) do update
set
  governance_status = excluded.governance_status,
  precedent_availability = excluded.precedent_availability,
  precedent_type = excluded.precedent_type,
  evidence_strength = excluded.evidence_strength,
  historical_event_status = excluded.historical_event_status,
  temporal_precision = excluded.temporal_precision,
  event_date_start = excluded.event_date_start,
  event_date_end = excluded.event_date_end,
  temporal_note = excluded.temporal_note,
  curated_narrative = excluded.curated_narrative,
  confidentiality_level_id = excluded.confidentiality_level_id,
  personal_information_status = excluded.personal_information_status,
  personal_information_notes = excluded.personal_information_notes,
  contains_historical_value_only_content = excluded.contains_historical_value_only_content,
  supersedes_version_id = excluded.supersedes_version_id,
  activated_at = excluded.activated_at;

with historical_case_seed (
  case_code,
  locator,
  confidentiality_level_code,
  evidence_strength,
  supported_claim_dimensions,
  relationship_notes
) as (
  values
    ('HC-001', 'Case 01: Merrachi Multi-Day Retail Pop-Up', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-001.'),
    ('HC-002', 'Case 02: Philips Coffee Machine Showcase', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-002.'),
    ('HC-003', 'Case 03: WineGB Trade & Press Showcase', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-003.'),
    ('HC-004', 'Case 04: Amoué PR Wellness Event', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-004.'),
    ('HC-005', 'Case 05: British Embassy / GreenTech Corporate Reception', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-005.'),
    ('HC-006', 'Case 06: Sheso Trading Event', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-006.'),
    ('HC-007', 'Case 07: MOOI / Little Wonderland PR Activation', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-007.'),
    ('HC-008', 'Vanessa Corporate Wellness Outing / Lululemon Branding Requirement', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective smaller-precedent section supporting the seeded Stage A identity and context for HC-008.'),
    ('HC-009', 'ADE Event: Permit, Alcohol, Sound & Operational Compliance', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective cautionary-precedent section supporting the seeded Stage A identity and context for HC-009.')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
historical_library_source as (
  select kso.id as source_object_id
  from public.knowledge_source_objects kso
  where kso.origin_type = 'repository_file'
    and kso.repository_relative_path = 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'
),
curated_role as (
  select hcer.id as evidence_role_id
  from public.historical_case_evidence_roles hcer
  where hcer.role_code = 'curated_case_library_source'
),
resolved_seed as (
  select
    tv.historical_case_version_id,
    hls.source_object_id,
    cr.evidence_role_id,
    kcl.id as confidentiality_level_id,
    hcs.locator,
    hcs.evidence_strength,
    hcs.supported_claim_dimensions,
    hcs.relationship_notes
  from historical_case_seed hcs
  join target_versions tv
    on tv.case_code = hcs.case_code
  cross join historical_library_source hls
  cross join curated_role cr
  join public.knowledge_confidentiality_levels kcl
    on kcl.level_code = hcs.confidentiality_level_code
)
delete from public.historical_case_version_source_objects hcvso
using target_versions tv,
      historical_library_source hls,
      curated_role cr
where hcvso.historical_case_version_id = tv.historical_case_version_id
  and hcvso.source_object_id = hls.source_object_id
  and hcvso.evidence_role_id = cr.evidence_role_id
  and not exists (
    select 1
    from resolved_seed rs
    where rs.historical_case_version_id = hcvso.historical_case_version_id
      and rs.source_object_id = hcvso.source_object_id
      and rs.evidence_role_id = hcvso.evidence_role_id
      and private.normalize_historical_case_source_locator(rs.locator) = private.normalize_historical_case_source_locator(hcvso.source_locator)
  );

with historical_case_seed (
  case_code,
  locator,
  confidentiality_level_code,
  evidence_strength,
  supported_claim_dimensions,
  relationship_notes
) as (
  values
    ('HC-001', 'Case 01: Merrachi Multi-Day Retail Pop-Up', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-001.'),
    ('HC-002', 'Case 02: Philips Coffee Machine Showcase', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-002.'),
    ('HC-003', 'Case 03: WineGB Trade & Press Showcase', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-003.'),
    ('HC-004', 'Case 04: Amoué PR Wellness Event', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-004.'),
    ('HC-005', 'Case 05: British Embassy / GreenTech Corporate Reception', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-005.'),
    ('HC-006', 'Case 06: Sheso Trading Event', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-006.'),
    ('HC-007', 'Case 07: MOOI / Little Wonderland PR Activation', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-007.'),
    ('HC-008', 'Vanessa Corporate Wellness Outing / Lululemon Branding Requirement', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective smaller-precedent section supporting the seeded Stage A identity and context for HC-008.'),
    ('HC-009', 'ADE Event: Permit, Alcohol, Sound & Operational Compliance', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective cautionary-precedent section supporting the seeded Stage A identity and context for HC-009.')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
historical_library_source as (
  select kso.id as source_object_id
  from public.knowledge_source_objects kso
  where kso.origin_type = 'repository_file'
    and kso.repository_relative_path = 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'
),
curated_role as (
  select hcer.id as evidence_role_id
  from public.historical_case_evidence_roles hcer
  where hcer.role_code = 'curated_case_library_source'
),
resolved_seed as (
  select
    tv.historical_case_version_id,
    hls.source_object_id,
    cr.evidence_role_id,
    kcl.id as confidentiality_level_id,
    hcs.locator,
    hcs.evidence_strength,
    hcs.supported_claim_dimensions,
    hcs.relationship_notes
  from historical_case_seed hcs
  join target_versions tv
    on tv.case_code = hcs.case_code
  cross join historical_library_source hls
  cross join curated_role cr
  join public.knowledge_confidentiality_levels kcl
    on kcl.level_code = hcs.confidentiality_level_code
)
update public.historical_case_version_source_objects hcvso
set
  confidentiality_level_id = rs.confidentiality_level_id,
  evidence_strength = rs.evidence_strength,
  source_locator = rs.locator,
  supported_claim_dimensions = rs.supported_claim_dimensions,
  relationship_notes = rs.relationship_notes
from resolved_seed rs
where hcvso.historical_case_version_id = rs.historical_case_version_id
  and hcvso.source_object_id = rs.source_object_id
  and hcvso.evidence_role_id = rs.evidence_role_id
  and private.normalize_historical_case_source_locator(hcvso.source_locator) = private.normalize_historical_case_source_locator(rs.locator);

with historical_case_seed (
  case_code,
  locator,
  confidentiality_level_code,
  evidence_strength,
  supported_claim_dimensions,
  relationship_notes
) as (
  values
    ('HC-001', 'Case 01: Merrachi Multi-Day Retail Pop-Up', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-001.'),
    ('HC-002', 'Case 02: Philips Coffee Machine Showcase', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-002.'),
    ('HC-003', 'Case 03: WineGB Trade & Press Showcase', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-003.'),
    ('HC-004', 'Case 04: Amoué PR Wellness Event', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-004.'),
    ('HC-005', 'Case 05: British Embassy / GreenTech Corporate Reception', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-005.'),
    ('HC-006', 'Case 06: Sheso Trading Event', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-006.'),
    ('HC-007', 'Case 07: MOOI / Little Wonderland PR Activation', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective library section supporting the seeded Stage A identity and context for HC-007.'),
    ('HC-008', 'Vanessa Corporate Wellness Outing / Lululemon Branding Requirement', 'commercially_sensitive', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective smaller-precedent section supporting the seeded Stage A identity and context for HC-008.'),
    ('HC-009', 'ADE Event: Permit, Alcohol, Sound & Operational Compliance', 'restricted', 'moderate', array['identity', 'responsibility', 'decision', 'lesson', 'context']::text[], 'Curated retrospective cautionary-precedent section supporting the seeded Stage A identity and context for HC-009.')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
historical_library_source as (
  select kso.id as source_object_id
  from public.knowledge_source_objects kso
  where kso.origin_type = 'repository_file'
    and kso.repository_relative_path = 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'
),
curated_role as (
  select hcer.id as evidence_role_id
  from public.historical_case_evidence_roles hcer
  where hcer.role_code = 'curated_case_library_source'
)
insert into public.historical_case_version_source_objects (
  historical_case_version_id,
  source_object_id,
  evidence_role_id,
  confidentiality_level_id,
  evidence_strength,
  source_locator,
  supported_claim_dimensions,
  relationship_notes
)
select
  tv.historical_case_version_id,
  hls.source_object_id,
  cr.evidence_role_id,
  kcl.id,
  hcs.evidence_strength,
  hcs.locator,
  hcs.supported_claim_dimensions,
  hcs.relationship_notes
from historical_case_seed hcs
join target_versions tv
  on tv.case_code = hcs.case_code
cross join historical_library_source hls
cross join curated_role cr
join public.knowledge_confidentiality_levels kcl
  on kcl.level_code = hcs.confidentiality_level_code
where not exists (
  select 1
  from public.historical_case_version_source_objects existing_source_link
  where existing_source_link.historical_case_version_id = tv.historical_case_version_id
    and existing_source_link.source_object_id = hls.source_object_id
    and existing_source_link.evidence_role_id = cr.evidence_role_id
    and private.normalize_historical_case_source_locator(existing_source_link.source_locator) = private.normalize_historical_case_source_locator(hcs.locator)
);

with topic_seed (
  case_code,
  topic_code,
  topic_relevance
) as (
  values
    ('HC-001', 'venue_clearing', 'primary'),
    ('HC-001', 'storage', 'primary'),
    ('HC-001', 'offsite_storage', 'primary'),
    ('HC-001', 'responsibility_boundaries', 'primary'),
    ('HC-001', 'client_operated_events', 'primary'),
    ('HC-001', 'class_schedule_interaction', 'secondary'),
    ('HC-002', 'technical_assessment', 'primary'),
    ('HC-002', 'electrical_load', 'primary'),
    ('HC-002', 'materials_cleanup_damage', 'primary'),
    ('HC-002', 'catering_supplier_coordination', 'secondary'),
    ('HC-003', 'storage', 'primary'),
    ('HC-003', 'offsite_storage', 'primary'),
    ('HC-003', 'responsibility_boundaries', 'primary'),
    ('HC-003', 'client_operated_events', 'secondary'),
    ('HC-003', 'production_coordination', 'primary'),
    ('HC-004', 'catering_supplier_coordination', 'primary'),
    ('HC-004', 'branding_restrictions', 'primary'),
    ('HC-004', 'storage', 'secondary'),
    ('HC-005', 'responsibility_boundaries', 'primary'),
    ('HC-005', 'catering_supplier_coordination', 'primary'),
    ('HC-005', 'alcohol_beverage_boundaries', 'primary'),
    ('HC-005', 'technical_assessment', 'secondary'),
    ('HC-005', 'client_operated_events', 'secondary'),
    ('HC-006', 'storage', 'primary'),
    ('HC-006', 'responsibility_boundaries', 'secondary'),
    ('HC-006', 'production_access', 'primary'),
    ('HC-006', 'overtime', 'primary'),
    ('HC-006', 'venue_clearing', 'secondary'),
    ('HC-007', 'production_access', 'primary'),
    ('HC-007', 'materials_cleanup_damage', 'primary'),
    ('HC-007', 'production_coordination', 'secondary'),
    ('HC-008', 'branding_restrictions', 'primary'),
    ('HC-008', 'class_schedule_interaction', 'primary'),
    ('HC-009', 'permits_compliance', 'primary'),
    ('HC-009', 'alcohol_beverage_boundaries', 'secondary'),
    ('HC-009', 'technical_assessment', 'secondary')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
resolved_topic_seed as (
  select
    tv.historical_case_version_id,
    hpt.id as topic_id,
    ts.topic_relevance
  from topic_seed ts
  join target_versions tv
    on tv.case_code = ts.case_code
  join public.historical_precedent_topics hpt
    on hpt.topic_code = ts.topic_code
)
delete from public.historical_case_version_topics hcvt
using target_versions tv
where hcvt.historical_case_version_id = tv.historical_case_version_id
  and not exists (
    select 1
    from resolved_topic_seed rts
    where rts.historical_case_version_id = hcvt.historical_case_version_id
      and rts.topic_id = hcvt.topic_id
  );

with topic_seed (
  case_code,
  topic_code,
  topic_relevance
) as (
  values
    ('HC-001', 'venue_clearing', 'primary'),
    ('HC-001', 'storage', 'primary'),
    ('HC-001', 'offsite_storage', 'primary'),
    ('HC-001', 'responsibility_boundaries', 'primary'),
    ('HC-001', 'client_operated_events', 'primary'),
    ('HC-001', 'class_schedule_interaction', 'secondary'),
    ('HC-002', 'technical_assessment', 'primary'),
    ('HC-002', 'electrical_load', 'primary'),
    ('HC-002', 'materials_cleanup_damage', 'primary'),
    ('HC-002', 'catering_supplier_coordination', 'secondary'),
    ('HC-003', 'storage', 'primary'),
    ('HC-003', 'offsite_storage', 'primary'),
    ('HC-003', 'responsibility_boundaries', 'primary'),
    ('HC-003', 'client_operated_events', 'secondary'),
    ('HC-003', 'production_coordination', 'primary'),
    ('HC-004', 'catering_supplier_coordination', 'primary'),
    ('HC-004', 'branding_restrictions', 'primary'),
    ('HC-004', 'storage', 'secondary'),
    ('HC-005', 'responsibility_boundaries', 'primary'),
    ('HC-005', 'catering_supplier_coordination', 'primary'),
    ('HC-005', 'alcohol_beverage_boundaries', 'primary'),
    ('HC-005', 'technical_assessment', 'secondary'),
    ('HC-005', 'client_operated_events', 'secondary'),
    ('HC-006', 'storage', 'primary'),
    ('HC-006', 'responsibility_boundaries', 'secondary'),
    ('HC-006', 'production_access', 'primary'),
    ('HC-006', 'overtime', 'primary'),
    ('HC-006', 'venue_clearing', 'secondary'),
    ('HC-007', 'production_access', 'primary'),
    ('HC-007', 'materials_cleanup_damage', 'primary'),
    ('HC-007', 'production_coordination', 'secondary'),
    ('HC-008', 'branding_restrictions', 'primary'),
    ('HC-008', 'class_schedule_interaction', 'primary'),
    ('HC-009', 'permits_compliance', 'primary'),
    ('HC-009', 'alcohol_beverage_boundaries', 'secondary'),
    ('HC-009', 'technical_assessment', 'secondary')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
insert into public.historical_case_version_topics (
  historical_case_version_id,
  topic_id,
  topic_relevance
)
select
  tv.historical_case_version_id,
  hpt.id,
  ts.topic_relevance
from topic_seed ts
join target_versions tv
  on tv.case_code = ts.case_code
join public.historical_precedent_topics hpt
  on hpt.topic_code = ts.topic_code
on conflict (historical_case_version_id, topic_id) do update
set topic_relevance = excluded.topic_relevance;

with rental_type_seed (
  case_code,
  rental_type_code
) as (
  values
    ('HC-001', 'entire_venue'),
    ('HC-006', 'entire_venue'),
    ('HC-007', 'entire_venue'),
    ('HC-008', 'studio_space')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
resolved_rental_type_seed as (
  select
    tv.historical_case_version_id,
    rt.id as rental_type_id
  from rental_type_seed rts
  join target_versions tv
    on tv.case_code = rts.case_code
  join public.rental_types rt
    on rt.rental_type_code = rts.rental_type_code
)
delete from public.historical_case_version_rental_types hcvrt
using target_versions tv
where hcvrt.historical_case_version_id = tv.historical_case_version_id
  and not exists (
    select 1
    from resolved_rental_type_seed rrts
    where rrts.historical_case_version_id = hcvrt.historical_case_version_id
      and rrts.rental_type_id = hcvrt.rental_type_id
  );

with rental_type_seed (
  case_code,
  rental_type_code
) as (
  values
    ('HC-001', 'entire_venue'),
    ('HC-006', 'entire_venue'),
    ('HC-007', 'entire_venue'),
    ('HC-008', 'studio_space')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
insert into public.historical_case_version_rental_types (
  historical_case_version_id,
  rental_type_id
)
select
  tv.historical_case_version_id,
  rt.id
from rental_type_seed rts
join target_versions tv
  on tv.case_code = rts.case_code
join public.rental_types rt
  on rt.rental_type_code = rts.rental_type_code
on conflict (historical_case_version_id, rental_type_id) do nothing;

with space_seed (
  case_code,
  space_code
) as (
  values
    ('HC-001', 'studio_space'),
    ('HC-001', 'one_to_one_room'),
    ('HC-001', 'retail_area'),
    ('HC-001', 'storage_room'),
    ('HC-001', 'back_office'),
    ('HC-004', 'one_to_one_room'),
    ('HC-006', 'retail_area')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
resolved_space_seed as (
  select
    tv.historical_case_version_id,
    vs.id as venue_space_id
  from space_seed ss
  join target_versions tv
    on tv.case_code = ss.case_code
  join public.venue_spaces vs
    on vs.space_code = ss.space_code
)
delete from public.historical_case_version_spaces hcvs
using target_versions tv
where hcvs.historical_case_version_id = tv.historical_case_version_id
  and not exists (
    select 1
    from resolved_space_seed rss
    where rss.historical_case_version_id = hcvs.historical_case_version_id
      and rss.venue_space_id = hcvs.venue_space_id
  );

with space_seed (
  case_code,
  space_code
) as (
  values
    ('HC-001', 'studio_space'),
    ('HC-001', 'one_to_one_room'),
    ('HC-001', 'retail_area'),
    ('HC-001', 'storage_room'),
    ('HC-001', 'back_office'),
    ('HC-004', 'one_to_one_room'),
    ('HC-006', 'retail_area')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
insert into public.historical_case_version_spaces (
  historical_case_version_id,
  venue_space_id
)
select
  tv.historical_case_version_id,
  vs.id
from space_seed ss
join target_versions tv
  on tv.case_code = ss.case_code
join public.venue_spaces vs
  on vs.space_code = ss.space_code
on conflict (historical_case_version_id, venue_space_id) do nothing;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_knowledge_document_versions hcvkdv
using target_versions tv
where hcvkdv.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_knowledge_documents hcvkd
using target_versions tv
where hcvkd.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_rule_versions hcvrv
using target_versions tv
where hcvrv.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_logical_rules hcvlr
using target_versions tv
where hcvlr.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_responsibility_sources hcvrs
using target_versions tv
where hcvrs.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_decision_sources hcvds
using target_versions tv
where hcvds.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_lesson_sources hcvls
using target_versions tv
where hcvls.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_lessons hcvl
using target_versions tv
where hcvl.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_decisions hcvd
using target_versions tv
where hcvd.historical_case_version_id = tv.historical_case_version_id;

with target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
delete from public.historical_case_version_responsibilities hcvr
using target_versions tv
where hcvr.historical_case_version_id = tv.historical_case_version_id;

with responsibility_seed (
  case_code,
  actor_type,
  responsibility_statement,
  evidence_strength,
  historical_value_only,
  contamination_risk_level,
  current_authority_disposition
) as (
  values
    ('HC-001', 'wnc', 'WNC cleared agreed venue areas and moved WNC stock, furniture, equipment, kitchen items, and Back Office contents out of sight.', 'strong', false, 'medium', 'check_phase_4'),
    ('HC-001', 'wnc', 'WNC prepared the venue for white-box handover and managed the transition from normal WNC operations into the rental.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-001', 'client', 'The client handled event operation, drinks, cleaning, products, and day-to-day operation after handover.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-002', 'wnc', 'WNC handled venue preparation and agreed venue clearing.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-002', 'wnc', 'WNC handled cleaning for the event.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-002', 'wnc', 'WNC removed the venue rocks and temporarily stored them before the event.', 'strong', true, 'medium', 'no_current_rule_implication'),
    ('HC-002', 'client', 'The client brought coffee machines, production equipment, and technical production requirements.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-002', 'client', 'The client production team and suppliers ran the showcase production.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-003', 'wnc', 'WNC handled venue preparation and agreed production setup.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-003', 'wnc', 'WNC coordinated furniture and equipment where included.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-003', 'wnc', 'WNC coordinated suppliers, deliveries, and storage.', 'strong', false, 'medium', 'check_phase_4_and_5'),
    ('HC-003', 'wnc', 'WNC provided venue cleanliness and operational support.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-003', 'wnc', 'WNC could include floral arrangement support where agreed.', 'strong', true, 'high', 'current_status_unknown'),
    ('HC-003', 'client', 'The client ran the trade showcase, hosted attendees, and owned guest-facing event operation.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-003', 'external_supplier', 'External suppliers handled catering and hired production items where applicable.', 'strong', false, 'low', 'check_phase_4_and_5'),
    ('HC-004', 'wnc', 'WNC provided the venue and practical overflow use of the 1:1 / Podcast Room.', 'moderate', false, 'medium', 'check_phase_4'),
    ('HC-004', 'client', 'The client controlled catering decisions and PR or brand-event operation.', 'moderate', false, 'medium', 'check_phase_5'),
    ('HC-004', 'client', 'The client negotiated commercial terms around discount or collaboration.', 'moderate', true, 'high', 'current_status_unknown'),
    ('HC-005', 'wnc', 'WNC provided the venue plus agreed catering and supplier coordination.', 'strong', false, 'low', 'check_phase_4_and_5'),
    ('HC-005', 'wnc', 'WNC provided agreed equipment support and operational guidance.', 'strong', false, 'medium', 'check_phase_4_and_5'),
    ('HC-005', 'client', 'The client owned event content, guests, and client-specific requirements.', 'strong', false, 'low', 'no_current_rule_implication'),
    ('HC-005', 'client', 'The client provided the wine for the reception.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-005', 'external_supplier', 'External suppliers supported catering or AV scope where engaged.', 'strong', false, 'medium', 'check_phase_4_and_5'),
    ('HC-006', 'wnc', 'WNC handled partial venue clearing and visible retail-stock removal needs.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-006', 'wnc', 'WNC provided onsite staff presence during build-up.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-006', 'client', 'The client handled build-up activity, event materials, and event operation.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-006', 'external_supplier', 'External suppliers supported catering and wellness elements where engaged.', 'moderate', false, 'medium', 'check_phase_5'),
    ('HC-007', 'wnc', 'WNC controlled venue access and the rental time boundary.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-007', 'wnc', 'WNC set cleanup and reset expectations and protected venue equipment.', 'strong', false, 'medium', 'check_phase_4_and_5'),
    ('HC-007', 'client', 'The client controlled setup activity and production materials.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-007', 'client', 'The client carried cleanup obligations for production materials.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-008', 'wnc', 'WNC provided an unbranded equipment option.', 'limited', true, 'medium', 'current_status_unknown'),
    ('HC-008', 'wnc', 'WNC managed the interaction with the existing class schedule.', 'limited', false, 'medium', 'check_phase_5'),
    ('HC-008', 'client', 'The client imposed branded-company and competitor-visibility constraints on the event experience.', 'limited', false, 'medium', 'no_current_rule_implication'),
    ('HC-009', 'wnc', 'WNC needed to trigger an early permit and compliance review for higher-impact ADE-style events.', 'limited', false, 'medium', 'check_phase_5')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
source_associations as (
  select
    hc.case_code,
    hcvso.historical_case_version_id,
    hcvso.id as historical_case_version_source_object_id
  from public.historical_case_version_source_objects hcvso
  join public.historical_case_versions hcv
    on hcv.id = hcvso.historical_case_version_id
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  join public.historical_case_evidence_roles hcer
    on hcer.id = hcvso.evidence_role_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
    and hcer.role_code = 'curated_case_library_source'
),
inserted_responsibilities as (
  insert into public.historical_case_version_responsibilities (
    historical_case_version_id,
    actor_type,
    responsibility_statement,
    evidence_strength,
    historical_value_only,
    contamination_risk_level,
    current_authority_disposition
  )
  select
    tv.historical_case_version_id,
    rs.actor_type,
    rs.responsibility_statement,
    rs.evidence_strength,
    rs.historical_value_only,
    rs.contamination_risk_level,
    rs.current_authority_disposition
  from responsibility_seed rs
  join target_versions tv
    on tv.case_code = rs.case_code
  returning
    id,
    historical_case_version_id,
    actor_type,
    responsibility_statement
)
insert into public.historical_case_version_responsibility_sources (
  historical_case_version_id,
  responsibility_id,
  historical_case_version_source_object_id
)
select
  tv.historical_case_version_id,
  ir.id,
  sa.historical_case_version_source_object_id
from responsibility_seed rs
join target_versions tv
  on tv.case_code = rs.case_code
join source_associations sa
  on sa.case_code = rs.case_code
 and sa.historical_case_version_id = tv.historical_case_version_id
join inserted_responsibilities ir
  on ir.historical_case_version_id = tv.historical_case_version_id
 and ir.actor_type = rs.actor_type
 and ir.responsibility_statement = rs.responsibility_statement;

with decision_seed (
  case_code,
  decision_statement,
  historical_context,
  evidence_strength,
  historical_value_only,
  contamination_risk_level,
  current_authority_disposition
) as (
  values
    ('HC-001', 'WNC cleared the venue and handed over a white-box-style space.', null, 'strong', false, 'medium', 'check_phase_4'),
    ('HC-001', 'External storage was used because onsite space was insufficient.', null, 'strong', true, 'high', 'potential_conflict_with_current_knowledge'),
    ('HC-001', 'After handover, the client largely ran its own event operations and support teams.', null, 'strong', false, 'medium', 'check_phase_4'),
    ('HC-002', 'WNC should not independently validate complex electrical load; client production should bring qualified technical assessment.', null, 'strong', false, 'low', 'check_phase_4'),
    ('HC-002', 'WNC removed the decorative rocks and stored them in the courtyard before the event.', null, 'strong', true, 'medium', 'no_current_rule_implication'),
    ('HC-002', 'WNC handled cleaning for the event.', null, 'strong', false, 'medium', 'check_phase_5'),
    ('HC-003', 'WNC provided real production coordination and physical setup.', null, 'strong', false, 'low', 'check_phase_4'),
    ('HC-003', 'External bike-storage / hallway storage was hired for EUR 300 for the day.', null, 'strong', true, 'high', 'potential_conflict_with_current_knowledge'),
    ('HC-003', 'Haylin could provide floral arrangement support where included.', null, 'strong', true, 'high', 'current_status_unknown'),
    ('HC-004', 'Strong-smelling food should be avoided for scent-sensitive beauty or perfume activations.', null, 'moderate', false, 'medium', 'check_phase_5'),
    ('HC-004', 'Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.', null, 'moderate', true, 'high', 'current_status_unknown'),
    ('HC-004', 'The 1:1 / Podcast Room was used as overflow storage in practice.', null, 'moderate', true, 'medium', 'check_phase_4'),
    ('HC-005', 'The client brought wine while other venue and service needs were part of planning.', null, 'strong', false, 'medium', 'check_phase_5'),
    ('HC-005', 'Responsibility for drinks, supply, and service needed to be explicit.', null, 'strong', false, 'low', 'check_phase_4'),
    ('HC-005', 'Corporate receptions can work at WNC without wellness programming.', null, 'strong', false, 'low', 'no_current_rule_implication'),
    ('HC-006', 'For one-day activations, storage volume must be discussed explicitly, not just whether storage is needed.', null, 'strong', false, 'medium', 'check_phase_5'),
    ('HC-006', 'Build-up hours need a firm end time.', null, 'strong', false, 'low', 'check_phase_4'),
    ('HC-006', 'If build-up runs late, additional WNC staffing or overtime should apply.', null, 'strong', true, 'high', 'check_phase_5'),
    ('HC-007', 'The 30-minute entire-venue grace period is for arrival, not free setup time.', null, 'strong', false, 'low', 'check_phase_4'),
    ('HC-007', 'Fake snow is not permitted.', null, 'strong', true, 'high', 'potential_conflict_with_current_knowledge'),
    ('HC-007', 'Other residue or damage-prone materials should be discussed in advance.', null, 'strong', false, 'medium', 'check_phase_5'),
    ('HC-008', 'WNC confirmed that unbranded equipment could be used.', null, 'limited', true, 'medium', 'current_status_unknown'),
    ('HC-008', 'Competitor-brand visibility mattered materially to the client.', null, 'limited', false, 'medium', 'no_current_rule_implication'),
    ('HC-009', 'Events involving DJs, amplified music, alcohol, non-standard guest use, or public-space activity should trigger early permit and compliance review.', null, 'limited', false, 'medium', 'check_phase_5'),
    ('HC-009', 'The historical ADE solution is not current legal precedent.', null, 'limited', true, 'high', 'potential_conflict_with_current_knowledge')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
source_associations as (
  select
    hc.case_code,
    hcvso.historical_case_version_id,
    hcvso.id as historical_case_version_source_object_id
  from public.historical_case_version_source_objects hcvso
  join public.historical_case_versions hcv
    on hcv.id = hcvso.historical_case_version_id
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  join public.historical_case_evidence_roles hcer
    on hcer.id = hcvso.evidence_role_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
    and hcer.role_code = 'curated_case_library_source'
),
inserted_decisions as (
  insert into public.historical_case_version_decisions (
    historical_case_version_id,
    decision_statement,
    historical_context,
    evidence_strength,
    historical_value_only,
    contamination_risk_level,
    current_authority_disposition
  )
  select
    tv.historical_case_version_id,
    ds.decision_statement,
    ds.historical_context,
    ds.evidence_strength,
    ds.historical_value_only,
    ds.contamination_risk_level,
    ds.current_authority_disposition
  from decision_seed ds
  join target_versions tv
    on tv.case_code = ds.case_code
  returning
    id,
    historical_case_version_id,
    decision_statement
)
insert into public.historical_case_version_decision_sources (
  historical_case_version_id,
  decision_id,
  historical_case_version_source_object_id
)
select
  tv.historical_case_version_id,
  idc.id,
  sa.historical_case_version_source_object_id
from decision_seed ds
join target_versions tv
  on tv.case_code = ds.case_code
join source_associations sa
  on sa.case_code = ds.case_code
 and sa.historical_case_version_id = tv.historical_case_version_id
join inserted_decisions idc
  on idc.historical_case_version_id = tv.historical_case_version_id
 and idc.decision_statement = ds.decision_statement;

with lesson_seed (
  case_code,
  lesson_kind,
  lesson_statement,
  evidence_strength,
  historical_value_only,
  contamination_risk_level,
  current_authority_disposition
) as (
  values
    ('HC-001', 'curated_lesson', 'Large takeovers need a detailed clearing and moving plan.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-001', 'curated_lesson', 'Clearing must be sequenced around WNC''s last normal operating day.', 'strong', false, 'medium', 'check_phase_4'),
    ('HC-001', 'curated_lesson', 'Offsite storage can become necessary when onsite capacity is insufficient.', 'strong', true, 'high', 'potential_conflict_with_current_knowledge'),
    ('HC-001', 'curated_lesson', 'Once fully handed over, a client-run takeover may not require ongoing WNC operational involvement.', 'strong', false, 'medium', 'check_phase_4'),
    ('HC-001', 'analyst_inference', 'Later modelling should separate handover complexity from guest-facing event complexity.', 'limited', false, 'low', 'no_current_rule_implication'),
    ('HC-002', 'curated_lesson', 'Collect power requirements per machine early.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-002', 'curated_lesson', 'Recommend qualified electrical assessment for heavy-load setups.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-002', 'curated_lesson', 'Major physical venue changes need lead time.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-002', 'curated_lesson', 'High-footfall catered events can create much more cleaning than expected.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-002', 'analyst_inference', 'Future precedent reasoning should separate technical feasibility confirmation from simple venue inventory availability.', 'limited', false, 'medium', 'check_phase_4'),
    ('HC-003', 'curated_lesson', 'Production coordination can include physical setup, not just emails.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-003', 'curated_lesson', 'Delivery dates and storage needs must be agreed before products arrive.', 'strong', false, 'low', 'check_phase_4_and_5'),
    ('HC-003', 'curated_lesson', 'Large-volume deliveries may require extra storage.', 'strong', false, 'medium', 'check_phase_4_and_5'),
    ('HC-003', 'curated_lesson', 'Clients should be asked how much must be stored, not just whether storage is needed.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-003', 'curated_lesson', 'Sourcing should happen early because items can go out of stock.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-003', 'curated_lesson', 'WNC support can remain venue and production focused without turning into guest-facing service.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-003', 'analyst_inference', 'This case supports distinguishing supported rental from full production in later modelling.', 'limited', false, 'low', 'check_phase_4'),
    ('HC-004', 'curated_lesson', 'Catering smell should match the intended guest experience.', 'moderate', false, 'medium', 'check_phase_5'),
    ('HC-004', 'curated_lesson', 'Scent-sensitive activations should avoid strong-smelling food.', 'moderate', false, 'medium', 'check_phase_5'),
    ('HC-004', 'caution_warning', 'WNC should not discount merely because a brand is new or offers exposure or gifts.', 'moderate', true, 'high', 'current_status_unknown'),
    ('HC-004', 'curated_lesson', 'Collaboration pricing should have a clear strategic reason.', 'moderate', true, 'high', 'current_status_unknown'),
    ('HC-004', 'analyst_inference', 'This case supports storing event-sensory-fit as a precedent topic even when no deterministic policy exists.', 'limited', false, 'low', 'no_current_rule_implication'),
    ('HC-005', 'curated_lesson', 'Drinks arrangements need explicit supply and service ownership.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-005', 'curated_lesson', 'Technical requirements should be identified before final handover.', 'strong', false, 'medium', 'check_phase_4_and_5'),
    ('HC-005', 'curated_lesson', 'Corporate receptions can fit the venue.', 'strong', false, 'low', 'no_current_rule_implication'),
    ('HC-005', 'curated_lesson', 'Responsibility boundaries matter even in relatively straightforward events.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-006', 'curated_lesson', 'Ask about approximate storage volume.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-006', 'curated_lesson', 'Many one-day activations keep WNC furniture but still need retail-stock clearing.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-006', 'curated_lesson', 'Create a clear storage destination for cleared materials.', 'strong', false, 'medium', 'check_phase_5'),
    ('HC-006', 'curated_lesson', 'Build-up hours need a firm end time.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-006', 'caution_warning', 'Late build-up should not create indefinite WNC onsite obligation.', 'strong', true, 'high', 'check_phase_5'),
    ('HC-006', 'analyst_inference', 'Later case modelling should allow both partial clearing and full clearing rather than flattening them into one whole-venue concept.', 'limited', false, 'low', 'check_phase_4'),
    ('HC-007', 'caution_warning', 'Grace period does not equal setup time, and the historical misuse must not be treated as a current setup allowance.', 'strong', true, 'high', 'check_phase_4'),
    ('HC-007', 'curated_lesson', 'If extra production time is needed, it must be included in the schedule.', 'strong', false, 'low', 'check_phase_4'),
    ('HC-007', 'caution_warning', 'Fake snow is prohibited in this historical precedent.', 'strong', true, 'high', 'potential_conflict_with_current_knowledge'),
    ('HC-007', 'curated_lesson', 'Production agencies need explicit timing, materials, and reset boundaries.', 'strong', false, 'medium', 'check_phase_4_and_5'),
    ('HC-007', 'analyst_inference', 'Future case modelling should distinguish access buffer from operational setup time.', 'limited', false, 'low', 'check_phase_4'),
    ('HC-008', 'curated_lesson', 'Ask about competitor-brand restrictions for branded-company events.', 'limited', false, 'medium', 'check_phase_5'),
    ('HC-008', 'curated_lesson', 'Minor logo or equipment details can matter significantly to the client.', 'limited', false, 'medium', 'check_phase_5'),
    ('HC-008', 'analyst_inference', 'Future case modelling may need a way to store brand-sensitivity constraints even when they do not map to Phase 4 rules.', 'limited', false, 'medium', 'no_current_rule_implication'),
    ('HC-009', 'caution_warning', 'High-impact or non-standard events need early permit and compliance review.', 'limited', false, 'medium', 'check_phase_5'),
    ('HC-009', 'caution_warning', 'Historical compliance solutions must not be reused without current legal checking.', 'limited', true, 'high', 'potential_conflict_with_current_knowledge'),
    ('HC-009', 'analyst_inference', 'Later modelling may need a distinct historical warning or caution concept separate from a normal operational lesson.', 'limited', false, 'low', 'no_current_rule_implication')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
),
source_associations as (
  select
    hc.case_code,
    hcvso.historical_case_version_id,
    hcvso.id as historical_case_version_source_object_id
  from public.historical_case_version_source_objects hcvso
  join public.historical_case_versions hcv
    on hcv.id = hcvso.historical_case_version_id
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  join public.historical_case_evidence_roles hcer
    on hcer.id = hcvso.evidence_role_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
    and hcer.role_code = 'curated_case_library_source'
),
inserted_lessons as (
  insert into public.historical_case_version_lessons (
    historical_case_version_id,
    lesson_kind,
    lesson_statement,
    evidence_strength,
    historical_value_only,
    contamination_risk_level,
    current_authority_disposition
  )
  select
    tv.historical_case_version_id,
    ls.lesson_kind,
    ls.lesson_statement,
    ls.evidence_strength,
    ls.historical_value_only,
    ls.contamination_risk_level,
    ls.current_authority_disposition
  from lesson_seed ls
  join target_versions tv
    on tv.case_code = ls.case_code
  returning
    id,
    historical_case_version_id,
    lesson_kind,
    lesson_statement
)
insert into public.historical_case_version_lesson_sources (
  historical_case_version_id,
  lesson_id,
  historical_case_version_source_object_id
)
select
  tv.historical_case_version_id,
  il.id,
  sa.historical_case_version_source_object_id
from lesson_seed ls
join target_versions tv
  on tv.case_code = ls.case_code
join source_associations sa
  on sa.case_code = ls.case_code
 and sa.historical_case_version_id = tv.historical_case_version_id
join inserted_lessons il
  on il.historical_case_version_id = tv.historical_case_version_id
 and il.lesson_kind = ls.lesson_kind
 and il.lesson_statement = ls.lesson_statement;

with logical_rule_seed (
  case_code,
  rule_code,
  relationship_code
) as (
  values
    ('HC-001', 'ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED', 'illustrates'),
    ('HC-001', 'ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'illustrates'),
    ('HC-001', 'ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED', 'illustrates'),
    ('HC-001', 'OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE', 'historical_precedent_for'),
    ('HC-001', 'OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL', 'historical_precedent_for'),
    ('HC-001', 'SERVICE_LEVEL_VENUE_ONLY', 'illustrates'),
    ('HC-002', 'TECH_REQ_HIGH_LOAD_POWER_CONFIRM', 'historical_precedent_for'),
    ('HC-002', 'TECH_REQ_CUSTOM_TECH_CONFIRM', 'historical_precedent_for'),
    ('HC-002', 'OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', 'illustrates'),
    ('HC-002', 'CATER_EXTERNAL_CATERER_ALLOWED', 'relevant_to'),
    ('HC-003', 'SERVICE_LEVEL_SUPPORTED_RENTAL', 'historical_precedent_for'),
    ('HC-003', 'SERVICE_ITEM_PRODUCTION_COORDINATION', 'historical_precedent_for'),
    ('HC-003', 'SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING', 'historical_precedent_for'),
    ('HC-003', 'OPER_DELIVERIES_WITHIN_RENTAL_WINDOW', 'illustrates'),
    ('HC-003', 'OPER_SUPPLIER_INFORMATION_REQUIRED', 'illustrates'),
    ('HC-003', 'CATER_EXTERNAL_CATERER_ALLOWED', 'relevant_to'),
    ('HC-004', 'ACCESS_STUDIO_ONE_TO_ONE_INCLUDED', 'illustrates'),
    ('HC-005', 'CATER_EXTERNAL_CATERER_ALLOWED', 'historical_precedent_for'),
    ('HC-005', 'TECH_REQ_BASIC_PROJECTION_CONFIRM', 'relevant_to'),
    ('HC-005', 'OPER_SUPPLIERS_CLIENT_RESPONSIBILITY', 'historical_precedent_for'),
    ('HC-005', 'OPER_SUPPLIER_INFORMATION_REQUIRED', 'historical_precedent_for'),
    ('HC-006', 'OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE', 'encountered_issue_related_to'),
    ('HC-006', 'OPER_SETUP_START_AT_BOOKED_TIME', 'encountered_issue_related_to'),
    ('HC-006', 'ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED', 'encountered_issue_related_to'),
    ('HC-007', 'OPER_ENTIRE_VENUE_GRACE_PERIOD', 'encountered_issue_related_to'),
    ('HC-007', 'OPER_SETUP_START_AT_BOOKED_TIME', 'encountered_issue_related_to'),
    ('HC-007', 'OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW', 'encountered_issue_related_to'),
    ('HC-009', 'TECH_REQ_AMPLIFIED_SOUND_EXTERNAL', 'relevant_to'),
    ('HC-009', 'TECH_REQ_DJ_AUDIO_EXTERNAL', 'relevant_to'),
    ('HC-009', 'TECH_REQ_MICROPHONE_USE_EXTERNAL', 'relevant_to')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
insert into public.historical_case_version_logical_rules (
  historical_case_version_id,
  rule_code,
  relationship_type_id,
  relationship_note
)
select
  tv.historical_case_version_id,
  lrs.rule_code,
  hcrrt.id,
  null
from logical_rule_seed lrs
join target_versions tv
  on tv.case_code = lrs.case_code
join public.historical_case_rule_relationship_types hcrrt
  on hcrrt.relationship_code = lrs.relationship_code;

with knowledge_document_seed (
  case_code,
  document_code,
  relationship_code
) as (
  values
    ('HC-001', 'CF-005', 'current_document_for_interpretation'),
    ('HC-001', 'CF-007', 'current_document_for_interpretation'),
    ('HC-001', 'OPS-002', 'current_context_relevant_to_case'),
    ('HC-001', 'TPL-010', 'current_guidance_to_consult'),
    ('HC-002', 'OPS-002', 'current_context_relevant_to_case'),
    ('HC-002', 'SERV-003', 'current_guidance_to_consult'),
    ('HC-002', 'CF-007', 'current_document_for_interpretation'),
    ('HC-002', 'TPL-008', 'current_guidance_to_consult'),
    ('HC-003', 'SERV-001', 'current_guidance_to_consult'),
    ('HC-003', 'SERV-003', 'current_guidance_to_consult'),
    ('HC-003', 'SERV-004', 'current_guidance_to_consult'),
    ('HC-003', 'TPL-007', 'current_guidance_to_consult'),
    ('HC-003', 'TPL-010', 'current_guidance_to_consult'),
    ('HC-004', 'SERV-003', 'current_guidance_to_consult'),
    ('HC-004', 'TPL-006', 'current_guidance_to_consult'),
    ('HC-004', 'TPL-003', 'current_guidance_to_consult'),
    ('HC-004', 'CF-007', 'current_document_for_interpretation'),
    ('HC-005', 'SERV-003', 'current_guidance_to_consult'),
    ('HC-005', 'SERV-004', 'current_guidance_to_consult'),
    ('HC-005', 'CF-007', 'current_document_for_interpretation'),
    ('HC-005', 'OPS-002', 'current_context_relevant_to_case'),
    ('HC-006', 'CF-005', 'current_document_for_interpretation'),
    ('HC-006', 'TPL-007', 'current_guidance_to_consult'),
    ('HC-006', 'TPL-009', 'current_guidance_to_consult'),
    ('HC-006', 'TPL-010', 'current_guidance_to_consult'),
    ('HC-006', 'SERV-001', 'current_guidance_to_consult'),
    ('HC-007', 'CF-005', 'current_document_for_interpretation'),
    ('HC-007', 'CF-007', 'current_document_for_interpretation'),
    ('HC-007', 'TPL-008', 'current_guidance_to_consult'),
    ('HC-007', 'TPL-010', 'current_guidance_to_consult'),
    ('HC-008', 'CF-003', 'current_document_for_interpretation'),
    ('HC-008', 'SERV-001', 'current_guidance_to_consult'),
    ('HC-008', 'TPL-007', 'current_guidance_to_consult'),
    ('HC-008', 'TPL-006', 'current_guidance_to_consult'),
    ('HC-009', 'CF-007', 'current_document_for_interpretation'),
    ('HC-009', 'SERV-001', 'current_guidance_to_consult'),
    ('HC-009', 'TPL-008', 'current_guidance_to_consult'),
    ('HC-009', 'TPL-010', 'current_guidance_to_consult')
),
target_versions as (
  select
    hc.case_code,
    hcv.id as historical_case_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
    and hcv.version_number = 1
)
insert into public.historical_case_version_knowledge_documents (
  historical_case_version_id,
  knowledge_document_id,
  relationship_type_id,
  relationship_note
)
select
  tv.historical_case_version_id,
  kd.id,
  hckrt.id,
  null
from knowledge_document_seed kds
join target_versions tv
  on tv.case_code = kds.case_code
join public.knowledge_documents kd
  on kd.document_code = kds.document_code
join public.historical_case_knowledge_relationship_types hckrt
  on hckrt.relationship_code = kds.relationship_code;

update public.historical_case_versions hcv
set governance_status = 'active'
from public.historical_cases hc
where hc.id = hcv.historical_case_id
  and hc.case_code in (
    'HC-001',
    'HC-002',
    'HC-003',
    'HC-004',
    'HC-005',
    'HC-006',
    'HC-007',
    'HC-008',
    'HC-009'
  )
  and hcv.version_number = 1
  and hcv.governance_status = 'draft';

select private.rebuild_current_historical_case_search_units();
