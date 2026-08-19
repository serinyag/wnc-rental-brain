# Future Enhancements

This register captures policy or automation improvements that may be useful later but do not block the current approved Phase 4 implementation.

Governance note:
- A blocker is an unresolved policy or source conflict that prevents the current slice from being implemented or from making a controlled decision the active scope requires.
- A deferred enhancement is useful additional structure, automation, or convenience that can wait without undermining the correctness of the current implemented slice.

| ID | Domain | Opportunity | Why this is not a blocker | Future decision or follow-up |
| -- | ------ | ----------- | ------------------------- | ---------------------------- |
| FE-001 | catering supplier / preferred supplier matrix | The current approved source set supports a WNC catering-partner path and external-caterer allowance, but it does not provide one controlled preferred, acceptable, or restricted supplier matrix by service category. | The current catering-supplier slice only needed to represent allowed arrangements, coordination defaults, kitchen limits, supplier-specific confirmation requirements, and VAT classification. Preferred-supplier ranking is a future workflow enhancement rather than a prerequisite for correct current policy storage. | Decide whether WNC wants a deterministic preferred, acceptable, or restricted supplier register by service category beyond the current partner path. |
| FE-002 | facilitator catalogue | The current service-facilitator slice intentionally excludes the individual `WNC Facilitators & Rental Experiences` catalogue until WNC agrees a curated menu of private-rental experience examples. | The current slice only needed facilitator-arrangement rules, confirmation semantics, and responsibility boundaries. It did not require live facilitator records, ranking, bios, or bookable experience products to represent the approved current policy correctly. | Approve the future curated facilitator and private-rental experience catalogue, including machine values, record ownership, and whether it belongs in governed source data or a later operational layer. |
