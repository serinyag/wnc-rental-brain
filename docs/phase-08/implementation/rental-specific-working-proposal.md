# Rental specific working proposals and Asana work

The console now builds a rental-specific proposal projection from persisted case facts, open questions, applicable requirements, decisions and proposed changes. It selects one of the five existing Word proposal templates and records the template path and content hash. The source templates remain unchanged. The live internal view and console detail response use this projection.

Venue scope and production service scope are separate. A studio booking can therefore use the Full Production template when full production is explicitly recorded. Unknown scope selects Custom Scope with a review warning. The seven existing proposal sections remain; detailed rows depend on recorded values, scope or specific outstanding questions and requirements. Unusual governed details are retained. Template placeholders do not establish prices, commitments or confirmations.

The observation registry accepts event schedules, production schedules, load-in windows, load-out windows and production scope through the existing validation boundary. These fields remain human-reviewed candidates. This does not add an autonomous email parser or let an agent approve its own observations. Dates, day counts and windows are preserved as structured values rather than inferred from a single booking interval.

Recorded requests remain TBC. Explicit `none` is shown as Not applicable. Existing accepted operational outcomes remain separate and must satisfy their original immutable evidence and scope checks. Completing an Asana checkbox cannot confirm a proposal detail. Proposal artifact freshness continues to depend on the case revision.

The new Asana layout includes only departments that contain governed work. Tasks still originate from the existing resolution actions, preserving their identities, owners and bindings. Follow-up work is added to the same master task. Existing certified layouts retain their original version and replay identities. The adapter continues to block silent reparenting, dropping unresolved work, human edit conflicts and ambiguous provider outcomes.

The production image definition includes only the five proposal source templates. No deployment, runtime gate change or real provider call is part of this implementation. Google Docs synchronization is explicitly disabled; the live internal view is the supported projection surface until a governed document writer is connected.

Validation covers all five template selections, simple versus production rentals, outstanding questions activating specific missing details, unusual scope, source provenance, HTML escaping, changing guest count, added supplier work, preserved Asana task bindings and replay without duplicates. The existing adapter tests retain ambiguity and migration coverage.
