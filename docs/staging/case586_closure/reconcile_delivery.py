from journey import *
assert not (OUT/'provider_receipt.json').exists(), 'Receipt already recorded; do not repeat this one-shot proof.'
proof=client().request('GET','/api/operator/cases/586/final-receipt')
save('provider_receipt',proof)
assert proof['receipt_verified'] and proof['exact_content_match'] and proof['provider_mutations']==0
candidate=json.loads((OUT/'final_candidate.json').read_text())
r=candidate['revision']
submission={'draft_revision_id':'387','approval_request_id':'466','execution_attempt_id':'29',
 'recipient':r['recipient_email'],'subject':r['subject'],
 'evidence_note':('Authorized synthetic operator receipt confirmation for Case 586 only. No human inbox observation is asserted. '
   'Bounded read-only Microsoft Graph verification matched the exact approved subject/body/sole recipient in both sent and Inbox copies, '
   'with identical Internet message ID and conversation. Inbox message '+proof['inbox_message_id']+' was received at '+proof['received_at']+
   '; Internet message ID '+proof['internet_message_id']+'. Original attempt 29 ambiguity and retry prohibition remain unchanged. '
   'No resend, new attempt, commercial commitment, or production effect.')}
save('delivery_confirmation_submission',submission)
first=call('delivery_confirmed','/api/operator/cases/586/actions/1640/confirm-delivery',submission)
assert first['ok']
second=call('delivery_confirmed_replay','/api/operator/cases/586/actions/1640/confirm-delivery',submission)
assert second['ok'] and 'Already reconciled: True' in second['report']['lines']
