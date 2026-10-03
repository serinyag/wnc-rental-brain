"""Provider-free, fail-closed completeness checks for selected governed answers.

These witnesses establish realization, not truth. Safety validation must pass
first. Unknown mandatory shapes remain unmet instead of silently becoming optional.
"""
from dataclasses import dataclass
from enum import StrEnum
from .pending_action_composition import CHANGE_SUBJECTS, change_subject_present
import re
from .editorial_content_planner import EditorialRole, EditorialContentItem, communication_evidence, mentioned, alias_matches, TOPIC_TERMS


class RealizationKind(StrEnum):
    QUESTION = 'question'
    KNOWN_FACT = 'known_fact'
    RESTRICTION = 'restriction'
    COMMERCIAL = 'commercial'
    PENDING_ACTION = 'pending_action'
    CONDITIONAL_CAPABILITY = 'conditional_capability'
    GUIDANCE = 'guidance'
    EXTERNAL_STATE = 'external_state'
    UNSUPPORTED = 'unsupported_required_semantics'


@dataclass(frozen=True)
class RealizationRequirement:
    item: EditorialContentItem
    kind: RealizationKind

    def to_payload(self):
        return {'semantic_key': self.item.semantic_key, 'topic': self.item.topic,
                'fingerprint': self.item.fingerprint, 'kind': self.kind.value,
                'required_meaning': self.item.value}


def requirements(plan):
    result = []
    for item in plan.items:
        if item.role not in {EditorialRole.MUST_ASK, EditorialRole.MUST_COMMUNICATE}:
            continue
        v = item.value
        if item.role == EditorialRole.MUST_ASK: kind = RealizationKind.QUESTION
        elif v.get('fact_state') == 'known' or v.get('status') == 'within_limits': kind = RealizationKind.KNOWN_FACT
        elif v.get('status') == 'not_supported' or item.topic == 'restriction': kind = RealizationKind.RESTRICTION
        elif 'booking_fee' in v: kind = RealizationKind.COMMERCIAL
        elif item.topic == 'projection_display': kind = RealizationKind.CONDITIONAL_CAPABILITY
        elif item.topic == 'external_pending': kind = RealizationKind.EXTERNAL_STATE
        elif 'suitable_for' in v or 'within' in v: kind = RealizationKind.GUIDANCE
        elif v.get('action') or v.get('status') in {'check_required','pending','conditional'}: kind = RealizationKind.PENDING_ACTION
        else: kind = RealizationKind.UNSUPPORTED
        result.append(RealizationRequirement(item, kind))
    return tuple(result)


def sentences(body):
    # Preserve decimals and currency values; question spans retain their '?' marker.
    return tuple(s.strip() for s in re.findall(r'[^!?;\n]+[!?;]?|[^\n]+$', re.sub(r'(?<!excl)(?<!incl)\.(?!\d)', '\n', body.casefold())) if s.strip())


def question_realized(question, body):
    q = question.casefold()
    spans = [s for s in sentences(body) if '?' in s or re.search(r'\b(?:please|could you|let us know|tell us|share)\b', s)]
    # Finite components of existing governed intake questions, not arbitrary word overlap.
    groups = []
    for trigger, aliases in [
        (r'\b(?:date|day)\b', ('date','day')),
        (r'\b(?:start|begin)\b', ('start','begin','beginning')),
        (r'\b(?:finish|end)\b', ('finish','end','ending')),
        (r'\b(?:guests|people|headcount)\b', ('guests','people','headcount','group size')),
        (r'\b(?:space|scope)\b', ('space','room','venue','studio','area')),
        (r'\b(?:type|kind) of event\b', ('type of event','kind of event','planning','occasion')),
    ]:
        if re.search(trigger,q): groups.append(aliases)
    if not groups and 'time' in q: groups.append(('time','timing'))
    if not groups: return any(q.rstrip('?') in s for s in spans)
    return all(any(alias_matches(aliases,s) for s in spans) for aliases in groups)


def prospective_spans(body):
    return [s for s in sentences(body) if (re.search(
        r"\b(?:i|we)(?:['’]ll| will| can| need to)\s+(?:also\s+)?(?:check|review|confirm|find out|look into)|\b(?:i|we)['’]m?\s+checking\b|\b(?:not yet confirmed|subject to (?:review|confirmation))\b", s) or (re.search(r"\b(?:i|we)(?:['’]ll| will)\b",s) and re.search(r'\band (?:also )?check\b',s))
        or (s.startswith('to ') and 'check' in s and re.search(r'\b(?:could you|let me know)\b',s)))]


def pending_realized(item, body):
    spans = prospective_spans(body)
    v = item.value
    if item.topic == 'requested_change':
        if v.get('requested_change') in CHANGE_SUBJECTS:
            return any(change_subject_present(v['requested_change'], s) for s in spans)
        return any(re.search(r'\b(?:change|updated|new|timing|arrangement|request)\b', s) for s in spans)
    if item.topic in {'commercial_next_step','overall_pricing'}:
        aliases = ('fee','pricing','price','cost')
        if v.get('request') == 'booking fee adjustment':
            aliases = ('adjustment','waiver','waive','flexibility','reduction')
        return any(alias_matches(aliases,s) for s in spans)
    if item.topic == 'projection_detail':
        value = v.get('check_required','')
        return any(alias_matches((value, value.rstrip('s')),s) for s in spans)
    subjects = v.get('subjects') or [v.get('subject') or item.topic]
    def subject_present(subject,s):
        if 'facilitator' in subject:
            return mentioned('facilitator',s) and bool(re.search(r'\b(?:availability|available)\b',s)) and bool(re.search(r'\b(?:format|welcome|opening|session)\b',s))
        if 'availability' in subject: return bool(re.search(r'\b(?:availability|available)\b',s))
        if 'loading' in subject: return bool(re.search(r'\b(?:loading|unloading)\b',s))
        if 'handover' in subject: return 'handover' in s
        if 'arrival' in subject: return bool(re.search(r'\b(?:arrival|arrive)\b',s))
        if 'setup' in subject: return bool(re.search(r'\b(?:setup|set up|access)\b',s))
        if 'delivery' in subject: return bool(re.search(r'\b(?:delivery|deliveries|access)\b',s))
        if 'rig' in subject or 'custom equipment' in subject:
            return mentioned('other_technical',s) and bool(re.search(r'\b(?:safe|safely|safety)\b',s)) and bool(re.search(r'\b(?:install|installed|installation)\b',s)) and bool(re.search(r'\b(?:operate|operated|operation)\b',s))
        return mentioned(item.topic,s)
    return all(any(subject_present(subject,s) for s in spans) for subject in subjects)


def realized(requirement, body):
    item, kind = requirement.item, requirement.kind
    v = item.value
    if kind == RealizationKind.QUESTION: return question_realized(v['question'],body)
    if kind == RealizationKind.KNOWN_FACT: return communication_evidence(item,body)
    if kind == RealizationKind.COMMERCIAL:
        # Require the fee's own clause, including its VAT basis and supplied rate.
        fee_spans = [s for s in sentences(body) if re.search(r'\b(?:booking )?fee\b',s)]
        amount_ok = any(communication_evidence(item,s) for s in fee_spans)
        rate = re.search(r'\d+(?:[.,]\d+)?\s*%',v.get('vat',''))
        vat_ok = not rate or any('vat' in s and rate.group() in s for s in sentences(body))
        basis_ok = 'excl' not in v['booking_fee'].lower() or any(re.search(r'\b(?:excl|excluding|exclusive|plus)\b',s) and 'vat' in s for s in fee_spans)
        return amount_ok and vat_ok and basis_ok
    if kind == RealizationKind.PENDING_ACTION: return pending_realized(item,body)
    if kind == RealizationKind.CONDITIONAL_CAPABILITY:
        return any(mentioned('projection_display',s) and re.search(r'\b(?:setup|arrangement|practical)\b',s) for s in prospective_spans(body))
    if kind == RealizationKind.RESTRICTION:
        if item.topic == 'restriction': return v['text'].casefold() in body.casefold()
        return any(mentioned(item.topic,s) and re.search(r"\b(?:not (?:available|supported|provided)|unavailable|cannot provide|external supplier|own supplier|bring your own)\b",s) for s in sentences(body))
    if kind == RealizationKind.GUIDANCE:
        if 'suitable_for' in v:
            return any(communication_evidence(item,s) and re.search(r'\b(?:not|rather than|instead of)\b.{0,50}\b(?:large.scale|production|cooking)\b',s) for s in sentences(body))
        return any(communication_evidence(item,s) and re.search(r'\b(?:within|during)\b.{0,40}\brental\b',s) for s in sentences(body))
    if kind == RealizationKind.EXTERNAL_STATE:
        topics = [topic for topic in TOPIC_TERMS if mentioned(topic, v.get('subject', ''))]
        return v.get('contact_status') == 'CONTACTED_AWAITING_RESPONSE' and any(
            any(mentioned(topic,s) for topic in topics) and re.search(r'\b(?:waiting|awaiting)\b',s)
            for s in sentences(body))
    return False


def validate_required_realization(plan, body):
    return tuple({**r.to_payload(), 'realized': bool(realized(r,body))} for r in requirements(plan))
