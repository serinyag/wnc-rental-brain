"""Writing-only grouping of selected checks; original plan identities stay intact."""
from dataclasses import dataclass
import re
from .editorial_content_planner import EditorialRole, alias_matches, logistics_needs


CHANGE_SUBJECTS = {
    'guest count': ('guest count', ('guest count', 'group size', 'group', 'headcount', 'guests', 'people')),
    'requested rental scope': ('rental scope', ('rental scope', 'full venue', 'entire venue', 'whole venue', 'studio')),
    'requested reschedule is awaiting review': ('reschedule', ('reschedule', 'new timing', 'new date', 'date and time', 'requested move', 'revised timing')),
}


def change_subject_present(change, text):
    """Finite witnesses for each existing change kind, shared by composition and gate."""
    if change not in CHANGE_SUBJECTS:
        return False
    if alias_matches(CHANGE_SUBJECTS[change][1], text):
        return True
    return change == 'requested reschedule is awaiting review' and bool(re.search(
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|\b\d{1,2}:\d{2}\b', text, re.I))


@dataclass(frozen=True)
class PendingActionGroup:
    items: tuple
    subjects: tuple[str, ...]
    grouping_reason: str

    def writing_value(self):
        return {'topic': 'pending_action_group', 'action': 'check',
                'subjects': list(self.subjects), 'status': 'check_required',
                'report_back': True, 'grouping_reason': self.grouping_reason}


def pending_action_groups(plan, latest_client_message):
    """Only finite WNC-owned shapes explicitly represented in this turn qualify.

    Unknown, commercial, external, fact and question shapes never enter groups.
    The planner's requested-change and next-step reasons establish WNC ownership;
    an explicit different owner or turn binding overrides that default.
    """
    buckets = {}
    current_logistics = logistics_needs(latest_client_message)
    for item in plan.role_items(EditorialRole.MUST_COMMUNICATE):
        v = item.value
        if (v.get('owner', 'WNC_INTERNAL') != 'WNC_INTERNAL'
                or v.get('resolution_owner', 'WNC_INTERNAL') != 'WNC_INTERNAL'
                or v.get('turn', 'current') != 'current'
                or v.get('fact_state') == 'known'
                or v.get('status') != 'check_required'):
            continue
        change = v.get('requested_change')
        if (item.topic == 'requested_change'
                and item.reason == 'prevent_requested_change_becoming_confirmation'
                and change_subject_present(change, latest_client_message)):
            family, subjects = 'same_current_turn_related_update', (change,)
        elif (item.topic == 'next_step' and item.reason == 'immediate_wnc_owned_next_step'
              and v.get('action') == 'check'):
            subjects = tuple(v.get('subjects') or (v.get('subject'),))
            if not subjects or not all(s in current_logistics for s in subjects):
                continue
            family = 'same_current_turn_supplier_logistics'
        else:
            continue
        entries = buckets.setdefault(family, [])
        entries.append((item, subjects))
    groups = []
    for reason, entries in buckets.items():
        subjects = tuple(dict.fromkeys(s for _, values in entries for s in values))
        if len(subjects) > 1:
            groups.append(PendingActionGroup(tuple(i for i, _ in entries), subjects, reason))
    return tuple(groups)


def must_say_projection(plan, latest_client_message):
    groups = pending_action_groups(plan, latest_client_message)
    membership = {i.semantic_key: group for group in groups for i in group.items}
    values = []
    for item in plan.role_items(EditorialRole.MUST_COMMUNICATE):
        group = membership.get(item.semantic_key)
        if group is None:
            values.append(item.writing_value())
        elif item is group.items[0]:
            values.append(group.writing_value())
    return values
