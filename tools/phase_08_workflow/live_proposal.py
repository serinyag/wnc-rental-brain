"""Internal, read-only living proposal: current facts, governed outcomes and freshness.

A stable URL reads the current case snapshot each time. It does not approve a
proposal, share a document, or import an Asana completion as a confirmed fact.
"""
import json
import re
from html import escape as h
from .asana_projection import build_projection, DEPARTMENT_VERSION


def render_live_proposal(snapshot):
    case = snapshot.rental_case
    plan = build_projection(snapshot, workspace_gid='preview', project_gid='preview', version=DEPARTMENT_VERSION)
    facts = ''.join('<tr><td>'+h(f.field_code.replace('_', ' ').title())+'</td><td>'+h(
        f.value_payload if isinstance(f.value_payload, str) else json.dumps(f.value_payload, ensure_ascii=False))+
        '</td><td>Recorded from source · revision '+str(f.established_case_revision)+'</td></tr>'
        for f in sorted(snapshot.rental_case_facts, key=lambda f:f.field_code) if not f.field_code.startswith('operational_resolution:'))
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
            '<section><h2>Recorded client details</h2><table><thead><tr><th>Detail</th><th>Value</th><th>Evidence</th></tr></thead><tbody>'+facts+'</tbody></table></section>'
            '<section><h2>Verified operational outcomes</h2>'+lines(outcomes,'No verified operational outcomes recorded yet.')+'<h3>Resolved checks</h3>'+lines(confirmed,'No checks resolved yet.')+'</section>'
            '<section><h2>Pending checks and decisions</h2>'+lines(pending,'No unresolved checks recorded.')+'</section>'
            '<section><h2>Latest proposal</h2>'+proposal+'<p>This internal view does not approve or send a client proposal.</p></section>'
            '<p><a href="/cases/'+str(case.rental_case_id)+'">Open full rental case</a></p></body></html>')
