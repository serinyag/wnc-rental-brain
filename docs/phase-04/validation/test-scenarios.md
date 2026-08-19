# Test Scenarios

## Foundation Invariants

1. Insert the same `rule_code` with the same `rule_version` twice.
Expected result: failure.

2. Insert a rule with `effective_until` earlier than `effective_from`.
Expected result: failure.

3. Insert a rule that supersedes itself.
Expected result: failure.

4. Insert an active rule and commit without a primary or governance source link.
Expected result: failure.

5. Insert a provenance link to a missing source or missing rule.
Expected result: failure.

## Future Domain Scenarios

1. Known input to booking fee:
Input: `rental_type = studio_space`, `duration = 2 hours`
Expected rule: studio 1-3 hour booking fee applies.

2. Known input to payment timing:
Input: booking made 10 days before event, selected payment option is 30% upfront
Expected rule: the 30% path is unavailable; the query should resolve to the 100% within 24 hours confirmation requirement and no 70% final-balance rule.

3. Known input to expedited surcharge:
Input: confirmation occurs 14 days before the event
Expected rule: expedited surcharge applies at 10% of venue rental only, with 21% VAT and waiver authority restricted to the WNC rental point of contact.

4. Known input to cancellation:
Input: client cancellation occurs 30 days before the event
Expected rule: rental payments are non-refundable, booking fee remains non-refundable, production and coordination fees remain non-refundable, committed-cost handling remains category-specific, and no live refund amount is guessed.

5. Known input to capacity:
Input: `space = studio_space`, `configuration = movement`, `guest_count = 21`
Expected rule outcome: Studio movement capacity is `20`, so the evaluation returns `exceeds_capacity`.

6. Missing input to capacity:
Input: `space = studio_space`, `guest_count = 40`, `layout = unknown`
Expected rule outcome: `insufficient_information`.

7. Space access:
Input: `rental_type = studio_space`, request `space = retail_area`
Expected rule outcome: `shared`, with WNC retail operations still allowed to continue.

8. Restricted support space:
Input: `rental_type = studio_space`, request `space = back_office`
Expected rule outcome: `restricted`, with explicit preparation and confirmation requirements.

9. Included flex space:
Input: `rental_type = entire_venue`, request `space = one_to_one_room`
Expected rule outcome: `included`, with setup and furniture nuance preserved in the rule details.

10. Catering supplier requirements:
Input: `catering_arrangement = external_caterer`, `kitchen_use_requested = true`
Expected rule outcome: external caterer allowed, supplier-specific storage and power confirmation requirements apply, kitchen suitability rules apply, and insurance is not silently inferred.

11. Manual commercial domain:
Input: `service_level = full_production`
Expected result: no deterministic pricing rule returned; manual quote remains required.

12. Operational grace period:
Input: `rental_type = studio_space`, question `grace_period`
Expected rule outcome: `15` minutes with `arrival_departure_only`; no setup rights are implied.

13. Operational setup timing:
Input: `rental_type = entire_venue`, question `setup_start`
Expected rule outcome: setup begins at booked time, while earlier operational access requires explicit approval.

14. Support-space operations:
Input: `space = storage_room`
Expected rule outcome: client event access stays restricted, but conditional operational storage use can still be returned without contradicting the access model.

15. Cleaning uncertainty:
Input: event likely to create significant mess or residue
Expected rule outcome: `manual_review_required`, not an invented deterministic cleaning threshold.

16. Catering VAT classification:
Input: `vat_category = mixed_catering_split`
Expected rule outcome: product and service lines must be split rather than assigned one blended VAT rate.

17. Technical capability distinction:
Input: request `ordinary_audio_playback` versus `amplified_event_sound`
Expected rule outcome: ordinary playback supported through installed Sonos, while amplified event sound requires an external or client-provided solution.

18. Technical quantity check:
Input: `equipment_code = basic_projector`, `requested_quantity = 2`
Expected rule outcome: `insufficient_quantity`, while no event-capacity value is inferred from that quantity result.

19. Service level lookup:
Input: `service_level = supported_rental`
Expected rule outcome: current row returns `conditional`, with written scope and manual quote required rather than open-ended support responsibility.

20. Service item lookup:
Input: `service_type = facilitator_sourcing`
Expected rule outcome: current row returns conditional WNC coordination with availability and briefing still requiring confirmation.

21. Client-provided facilitator:
Input: `facilitator_arrangement = client_provided`
Expected rule outcome: arrangement is allowed, client responsibility remains explicit, and the system does not infer WNC coordination by default.

22. WNC-provided facilitator:
Input: `facilitator_arrangement = wnc_provided`
Expected rule outcome: arrangement is conditional, availability confirmation is required, and client commitment cannot be treated as final before that confirmation.

23. No facilitator:
Input: `facilitator_arrangement = none`
Expected rule outcome: `not_applicable`, with no facilitator-specific requirement triggered.

24. Unknown facilitator arrangement:
Input: `facilitator_arrangement = unknown`
Expected rule outcome: uncertainty is preserved and the system does not guess WNC provision or client provision.
