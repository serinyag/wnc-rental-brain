# Proposed bounded real inbound test — not sent or ingested

Sender: `Serinya@whennaturecalls.nl` (human-operated synthetic sender)
Recipient: `Serinya@whennaturecalls.nl` (the mailbox currently configured in staging)
Subject: `SYNTHETIC TEST — WNC Outlook inbound certification`

Exact initial body:

> Hi WNC,
>
> This is a synthetic staging test, not a real booking.
>
> We are enquiring about a Studio team workshop for 24 guests on 12 November 2026. We have not decided the start and finish times yet.
>
> We plan to use an external caterer and would like basic projection. Please let us know what information you need next.
>
> Thank you,
> Synthetic WNC client

Expected: one provider message, one immutable source record, one new synthetic case at the normal initial lifecycle, and one exact mailbox/conversation binding. Existing timing extraction handles the requested date using provider receipt time. Missing times remain unknown. Other prose remains auditable evidence and does not become business truth directly. No external task or outbound email executes.

After initial ingestion is separately authorized and verified, the human should reply in that same conversation with:

> Hi WNC,
>
> Continuing the same synthetic staging enquiry: please use 14:00 to 18:00 on 12 November 2026.
>
> Thank you,
> Synthetic WNC client

Expected follow-up: second provider message and source, same conversation and case, existing governed timing intake advances the case. Do not start a separate conversation. No email has been sent as part of implementation or preflight.
