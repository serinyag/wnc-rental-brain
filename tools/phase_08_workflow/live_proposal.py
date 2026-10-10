"""Internal, read-only living proposal: current facts, governed outcomes and freshness.

A stable URL reads the current case snapshot each time. It does not approve a
proposal, share a document, or import an Asana completion as a confirmed fact.
"""
import json
import re
from html import escape as h
from .asana_projection import _build_flat_projection
from .working_proposal import build_rental_working_proposal


def render_live_proposal(snapshot):
    case = snapshot.rental_case
    plan = _build_flat_projection(snapshot, workspace_gid='preview', project_gid='preview', enforce_limits=False)
    proposal_model = build_rental_working_proposal(snapshot)
    def value_text(value):
        return 'To be confirmed' if value is None else (value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))
    sections = []
    for section in proposal_model['sections']:
        if section in {'Confirmed / Still TBC', 'Next Steps'}:
            continue
        rows = [r for r in proposal_model['details'] if r['section'] == section]
        if rows:
            body = '<table><thead><tr><th>Detail</th><th>Current value</th><th>Status</th><th>Source</th></tr></thead><tbody>'
            body += ''.join('<tr><td>'+h(r['label'])+'</td><td>'+h(value_text(r['value']))+'</td><td>'+h(r['status'])+
                '</td><td>'+h(r['source_reference'] or 'Awaiting confirmation')+'</td></tr>' for r in rows)
            body += '</tbody></table>'
        else:
            body = '<p>No rental-specific details recorded for this section yet.</p>'
        sections.append('<section><h2>'+h(section)+'</h2>'+body+'</section>')
    facts = ''.join(sections)
    from .operational_resolution import current_resolutions
    outcomes = [subject + ": " + outcome.replace("_", " ").title() for r in current_resolutions(snapshot) for subject, outcome in r["outcomes"].items()]
    confirmed, pending = [], []
    for item in plan['work']:
        if item.get('kind') == 'department':continue
        for member in item['members']:
            (confirmed if member['resolved'] else pending).append(member['summary'])
    def lines(values, empty):
        return '<ul>'+''.join('<li>'+h(v)+'</li>' for v in dict.fromkeys(values))+'</ul>' if values else '<p>'+empty+'</p>'
    artifact = next((a for a in snapshot.artifacts if a.artifact_reference_id == case.current_proposal_artifact_id), None)
    proposal = '<p>No generated proposal is bound to this case yet.</p>'
    if artifact:
        fresh = artifact.derived_from_case_revision == case.case_revision and artifact.freshness_status == 'current'
        proposal = '<p>Proposal revision '+str(artifact.derived_from_case_revision)+' · '+('Current' if fresh else 'Stale — refresh and review required')+'</p>'
        reference = artifact.external_reference or artifact.storage_reference or ''
        if re.fullmatch(r'https://docs\.google\.com/document/d/[A-Za-z0-9_-]+/(?:edit|view)', reference):
            proposal += '<p><a rel="noreferrer" href="'+h(reference)+'">Open proposal in Google Docs</a></p>'
    pending += [q.human_question_text for q in snapshot.open_questions if q.status == 'open']
    pending += [r.requirement_type.replace('_', ' ') for r in snapshot.requirements if r.status in {'required','unresolved','in_progress'}]
    pending += [d.scope_description for d in snapshot.case_decisions if d.status in {'proposed','pending_approval'}]
    pending += ['Requested change awaiting review: '+c.change_kind.replace('_', ' ') for c in snapshot.proposed_changes if c.status in {'proposed','under_review'}]
    return ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="refresh" content="60"><title>Live rental details</title><style>'
            'body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 24px;color:#20232a;background:#f7f8fa}'
            'section{background:white;border:1px solid #dde1e6;border-radius:12px;padding:24px;margin:18px 0}'
            'td,th{text-align:left;padding:12px;border-bottom:1px solid #eee}table{width:100%}li{margin:10px 0}'
            'a{color:#3155ae}</style></head><body><h1>'+h(plan['master']['name'])+'</h1>'
            '<p>Internal working proposal · Case '+h(case.case_reference_code)+' · revision '+str(case.case_revision)+
            ' · '+h(case.lifecycle_state.replace('_',' '))+'</p><p>Updates from the current case every minute. Requested details are not booking confirmations.</p>'
            '<p>Template: '+h(proposal_model['template']['title'])+'</p>'+
            ('<p>Scope is unclear. Review the Custom Scope template choice before issuing a proposal.</p>' if proposal_model['template_review_required'] else '')+facts+
            '<section><h2>Confirmed / Still TBC</h2><h3>Verified operational outcomes</h3>'+lines(outcomes,'No verified operational outcomes recorded yet.')+'<h3>Resolved checks</h3>'+lines(confirmed,'No checks resolved yet.')+'</section>'
            '<section><h2>Next Steps</h2>'+lines(pending,'No unresolved checks recorded.')+'</section>'
            '<section><h2>Latest proposal</h2>'+proposal+'<p>This internal view does not approve or send a client proposal.</p></section>'
            '<p><a href="/cases/'+str(case.rental_case_id)+'">Open full rental case</a></p></body></html>')
