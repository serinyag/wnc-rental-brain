from __future__ import annotations

"""Deterministic editorial projection, never a source of facts or authority.

The complete governed contract remains local for validation. Only selected,
client-safe values cross the writing boundary. Topic selectors select existing
answers; they cannot establish capability, price, policy or approval.
"""
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
import hashlib
import json
import re
from typing import Any


class EditorialRole(StrEnum):
    MUST_COMMUNICATE = 'MUST_COMMUNICATE'
    MUST_ASK = 'MUST_ASK'
    ACKNOWLEDGE = 'ACKNOWLEDGE'
    HELPFUL_NOW = 'HELPFUL_NOW'
    ALREADY_COMMUNICATED = 'ALREADY_COMMUNICATED'
    DEFER = 'DEFER'
    INTERNAL_ONLY = 'INTERNAL_ONLY'


INCLUDED_ROLES = frozenset({EditorialRole.MUST_COMMUNICATE, EditorialRole.MUST_ASK,
                            EditorialRole.ACKNOWLEDGE, EditorialRole.HELPFUL_NOW})


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class EditorialContentItem:
    semantic_key: str
    topic: str
    source_reference: str
    proposition_key: str
    authority_class: str
    value: dict[str, Any]
    role: EditorialRole
    reason: str
    prior_turn_status: str = 'not_previously_communicated'
    priority: int = 50

    @property
    def fingerprint(self) -> str:
        return digest([self.semantic_key, self.source_reference, self.value])

    @property
    def included(self) -> bool:
        return self.role in INCLUDED_ROLES

    def to_payload(self) -> dict[str, Any]:
        return {**asdict(self), 'fingerprint': self.fingerprint, 'included_in_model_payload': self.included}

    def writing_value(self) -> dict[str, Any]:
        # No source/authority rationale or internal identifiers cross this boundary.
        return {'topic': self.topic, **self.value}


@dataclass(frozen=True)
class EditorialContentPlan:
    response_intent: str
    primary_client_need: tuple[str, ...]
    items: tuple[EditorialContentItem, ...]
    substantive_budget: int
    budget_reason: str
    version: str = 'editorial_content_plan_v3'

    def role_items(self, role: EditorialRole) -> tuple[EditorialContentItem, ...]:
        return tuple(item for item in self.items if item.role == role)

    @property
    def do_not_repeat(self) -> tuple[str, ...]:
        return tuple(item.topic for item in self.role_items(EditorialRole.ALREADY_COMMUNICATED))

    def to_payload(self) -> dict[str, Any]:
        return {'version': self.version, 'response_intent': self.response_intent,
                'primary_client_need': self.primary_client_need,
                **{role.value.lower(): [item.to_payload() for item in self.role_items(role)] for role in EditorialRole},
                'do_not_repeat': self.do_not_repeat,
                'client_visible_pending_state': [item.writing_value() for item in self.items if item.included and item.value.get('status') in {'check_required', 'pending', 'conditional'}],
                'substantive_budget': self.substantive_budget, 'editorial_rationale': self.budget_reason,
                'source_bindings': [{'semantic_key': i.semantic_key, 'source_reference': i.source_reference,
                                     'fingerprint': i.fingerprint} for i in self.items]}


# A finite adapter for request topics already used by Phase 8. These selectors
# decide attention only. All answers come from the governed contract below.
TOPIC_TERMS = {
    'audio_playback': ('music', 'audio', 'sound system', 'background sound', 'amplified sound'),
    'projection_display': ('projector', 'projectors', 'projection', 'slide', 'slides', 'screen', 'screens'),
    'microphones': ('microphone', 'microphones', 'mic', 'mics'),
    'dj_sound_booth': ('dj', 'dj setup', 'dj booth', 'sound booth'),
    'other_technical': ('hologram', 'holograms', 'aerial', 'rig', 'rigs', 'custom technical'),
    'catering_kitchen': ('caterer', 'caterers', 'catering', 'kitchen', 'food', 'buffet', 'lunch', 'cook', 'cooking'),
    'supplier_access': ('setup', 'set up', 'loading', 'unloading', 'delivery', 'deliveries', 'deliver', 'arrive', 'arrival', 'supplier', 'suppliers', 'handover', 'florist'),
    'facilitator': ('facilitator', 'facilitation', 'facilitate', 'host', 'welcome', 'opening'),
    'commercial': ('fee', 'fees', 'cost', 'costs', 'price', 'prices', 'pricing', 'waive', 'waiver', 'flexibility'),
    'capacity': ('fit', 'fits', 'capacity', 'accommodate', 'accommodation', 'suitable', 'suitability', 'enough room'),
}


def alias_matches(aliases: tuple[str, ...], text: str) -> bool:
    normalized = ' '.join(re.findall(r"\w+", text.casefold()))
    return any(re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', normalized) for alias in aliases)


def mentioned(topic: str, text: str) -> bool:
    return alias_matches(TOPIC_TERMS.get(topic, (topic.replace('_', ' '),)), text)


def pricing_context(text: str) -> dict[str, Any]:
    # A request for prices is not evidence that the client supplied a budget.
    budget = 'absent'
    if re.search(r'\b(?:budget|we have|we can spend)\b.{0,40}(?:\bEUR\s*\d|€\s*\d|\d[\d.,]*\s*(?:euros?|EUR)\b)', text, re.I):
        budget = 'explicit_amount'
    elif re.search(r'\bbudget\b', text, re.I):
        budget = 'general_constraint'
    requested = bool(re.search(r'\b(?:pricing|prices?|costs?)\b', text, re.I) and
                     re.search(r'\b(?:what|how|does|can|could|realistic|fit|send|tell)\b|\?', text, re.I))
    return {'overall_pricing_requested': requested, 'budget_context': budget}


def optional_client_delta(text: str) -> dict[str, Any] | None:
    for clause in re.split(r'[.!?\n]', text):
        for item in ('hologram', 'projection', 'aerial rig'):
            if alias_matches((item,), clause) and re.search(r'\boptional\b', clause, re.I):
                delta = {'kind': 'client_preference_change', 'item': item, 'optional': True}
                if re.search(r'(?:not|don.t) (?:hold up|delay)|should not delay', clause, re.I):
                    delta['should_not_delay'] = ['event planning']
                    if mentioned('projection_display', text) and item != 'projection':
                        delta['should_not_delay'].insert(0, 'projection planning')
                return delta
    return None


def asked_again(topic: str, text: str) -> bool:
    # A supplier logistics question does not reopen food preparation guidance.
    if topic == 'catering_kitchen' and logistics_needs(text) and not alias_matches(
            ('kitchen', 'food', 'cook', 'cooking', 'prepare', 'preparation', 'warming', 'plating', 'buffet'), text):
        return False
    # "The florist can arrive" is a new detail, not an explicit repeat question.
    return any(mentioned(topic, part) and ("?" in part or re.search(
        r'^\s*(?:can|could|would|what|how|is|are|does|please (?:confirm|explain|tell))\b', part, re.I))
        for part in re.split(r'[.!\n]', text))


def logistics_needs(text: str) -> tuple[str, ...]:
    """Specific request components, not the entire logistics policy category."""
    needs = []
    for part in re.split(r'[.!?\n]', text.lower()):
        for tokens, label in [(('loading', 'unload'), 'loading route'), (('handover',), 'venue handover'),
                              (('arrival', 'arrive'), 'supplier arrival timing'), (('deliver',), 'delivery access')]:
            if any(token in part for token in tokens):needs.append(label)
        if re.search(r'setup|set up', part) and re.search(r'cater|supplier|florist|\d+\s*(?:minutes?|min)', part):
            needs.append('supplier setup access')
    return tuple(dict.fromkeys(needs))


def client_acknowledges_restriction(topic: str, text: str) -> bool:
    return any(mentioned(topic, part) and re.search(r'\b(?:know|understand|fine)\b', part, re.I)
               and re.search(r'not available|not supported|unavailable', part, re.I)
               for part in re.split(r'[.!?\n]', text))


def client_question_value(question: str) -> str:
    # Exact existing application question semantics, with the internal label
    # removed. IDs and every required component remain in the local contract.
    return question.replace('space or rental scope', 'space').replace('is the client requesting', 'would you like').replace('is the client planning', 'are you planning')


def normalized_guidance(guide: Any) -> tuple[tuple[str, str, dict[str, Any]], ...]:
    """Project only recognized current source values; no broad document rewrite."""
    values = getattr(guide, 'semantic_values', None)
    if values:
        return ((values['topic'], values['topic'], {k: v for k, v in values.items() if k != 'topic'}),)
    text = guide.client_safe_guidance
    lower = text.lower()
    # Narrow projections of current governed service guidance. Unrecognized
    # source text stays auditable as DEFER, never invented as structured truth.
    if guide.source_reference == 'SERV-003' and 'best suited' in lower and 'warming' in lower:
        return (('catering_kitchen', 'catering_kitchen', {'suitable_for': ['ready-made food', 'warming', 'plating', 'simple assembly'],
                 'limitation': 'not large-scale food production'}),)
    if guide.source_reference == 'CF-005' and 'confirmed rental period' in lower and 'unloading' in lower:
        return (('supplier_access', 'supplier_access', {'activities': ['deliveries', 'unloading', 'setup'],
                 'within': 'confirmed rental period', 'exception': 'prior written agreement'}),)
    return ()


def communication_evidence(item: EditorialContentItem, body: str) -> bool:
    """Conservative realization witness, not a claim that an email was sent.

    Stable item identity/value fingerprint drive novelty. This small check avoids
    recording an omitted planned item as communicated. Unknown wording yields no
    evidence, so it cannot silently suppress a material answer on the next turn.
    """
    text = body.lower()
    if item.topic == 'commercial':
        amounts = re.findall(r'EUR\s*([\d.,]+)', json.dumps(item.value), re.I)
        return bool(amounts) and all(re.search(r'(?:eur|€)\s*' + re.escape(a), text) for a in amounts)
    if item.topic == 'capacity':
        return bool(re.search(r'\b(?:fit|suitable|capacity|accommodate)\b', text))
    if item.topic == 'catering_kitchen':
        return 'kitchen' in text and any(w in text for w in ('warming', 'plating', 'ready-made'))
    if item.topic == 'audio_playback':
        return mentioned(item.topic, text) and bool(re.search(r'\b(?:supported|fine|possible|can be played|available|no problem)\b', text))
    if item.topic == 'projection_display':
        return mentioned(item.topic, text) and bool(re.search(r'\b(?:projector|projection)\b.{0,25}\bavailable\b', text)) and bool(re.search(r'\b(?:check|checking)\b.{0,50}\b(?:setup|arrangement)\b', text))
    if item.topic == 'microphones':
        return mentioned(item.topic, text) and ('supplier' in text or 'external' in text)
    if item.topic == 'supplier_access':
        return 'rental' in text and any(w in text for w in ('setup', 'unloading', 'deliver'))
    return False


def communicated_items(plan: EditorialContentPlan, body: str) -> list[dict[str, str]]:
    return [{'semantic_key': item.semantic_key, 'fingerprint': item.fingerprint, 'topic': item.topic,
             'source_reference': item.source_reference}
            for item in plan.items if item.included and communication_evidence(item, body)]


def build_editorial_content_plan(contract: Any) -> EditorialContentPlan:
    latest = contract.latest_client_message
    earlier = '\n'.join(contract.prior_client_messages)
    current_topics = {topic for topic in TOPIC_TERMS if mentioned(topic, latest)}
    logistics = logistics_needs(latest)
    if 'supplier_access' in current_topics and not logistics:
        current_topics.discard('supplier_access')
    requested_topics = current_topics | {topic for topic in TOPIC_TERMS if mentioned(topic, earlier)}
    prior = {x['semantic_key']: x['fingerprint'] for x in getattr(contract, 'prior_editorial_items', ())}
    items: list[EditorialContentItem] = []

    def add(key: str, topic: str, value: dict[str, Any], role: EditorialRole, reason: str,
            source: str = 'governed_case', authority: str = 'current_governed', priority: int = 50,
            novelty: bool = False) -> None:
        item = EditorialContentItem(key, topic, source, key, authority, value, role, reason, priority=priority)
        prior_status = 'changed_since_prior_draft' if key in prior and prior[key] != item.fingerprint else 'not_previously_communicated'
        if novelty and prior.get(key) == item.fingerprint:
            prior_status = 'unchanged_answer_in_prior_draft'
            if not asked_again(topic, latest) and role != EditorialRole.INTERNAL_ONLY:
                item = replace(item, role=EditorialRole.ALREADY_COMMUNICATED, reason='unchanged_answer_already_explained')
            else:
                item = replace(item, reason='explicit_current_turn_question_requires_answer_again')
        items.append(replace(item, prior_turn_status=prior_status))

    # Every client-owned open question is mandatory, including multi-component
    # questions. No budget may drop it or move internal ownership to the client.
    for qid, question in contract.open_client_questions:
        add(f'question:{qid}', 'client_information', {'open_question_id': qid, 'question': client_question_value(question)},
            EditorialRole.MUST_ASK, 'open_client_owned_question', priority=2)

    event_type = next((x.split(': ', 1)[1] for x in contract.confirmed_case_facts if x.startswith('event_type: ')), None)
    acknowledgement = optional_client_delta(latest) or ({'kind': 'new_enquiry', 'about': event_type or 'the enquiry'} if not contract.prior_client_messages
                       else {'kind': 'new_client_detail', 'focus': 'the change or clarification in the latest message'})
    add('latest_client_detail', 'latest_client_detail', acknowledgement,
        EditorialRole.ACKNOWLEDGE, 'current_turn_delta', source='current_client_message', authority='client_request', priority=3)

    for state in contract.change_or_reschedule_state:
        add('change:' + digest(state)[:12], 'requested_change', {'requested_change': state, 'status': 'check_required', 'action': 'check the requested change and come back to the client'},
            EditorialRole.MUST_COMMUNICATE, 'prevent_requested_change_becoming_confirmation', priority=1)

    # A fee answer can become available several turns after its question. Stable
    # value identity prevents omission of a newly priced answer or changed price.
    terms = dict(text.split(': ', 1) for text in contract.allowed_client_assertions if ': ' in text)
    fee = terms.get('Effective booking fee') or terms.get('Booking fee baseline') or terms.get('Booking fee')
    commercial = {'booking_fee': fee, **({'vat': terms['VAT']} if terms.get('VAT') else {})} if fee else {}
    if commercial:
        add('commercial.current', 'commercial', commercial,
            EditorialRole.MUST_COMMUNICATE if 'commercial' in requested_topics else EditorialRole.DEFER,
            'current_or_unanswered_earlier_commercial_question' if 'commercial' in requested_topics else 'not_needed_for_current_question',
            priority=1, novelty=True)
    if 'commercial' in requested_topics and not commercial:
        add('commercial.check', 'commercial_next_step', {'action': 'check requested booking fee or pricing', 'status': 'check_required'},
            EditorialRole.MUST_COMMUNICATE, 'requested_answer_not_yet_available', priority=4)
    pricing = pricing_context(latest)
    if pricing['overall_pricing_requested']:
        action = 'check overall rental pricing for the requested event/options'
        if pricing['budget_context'] != 'absent':
            action += ' taking the stated budget into account'
        add('commercial.overall_pricing', 'overall_pricing', {**pricing, 'action': action, 'status': 'check_required'},
            EditorialRole.MUST_COMMUNICATE, 'overall_pricing_question_is_distinct_from_booking_fee', priority=1)
    for index, decision in enumerate(contract.pending_decisions):
        add('decision:' + decision, 'commercial_next_step', {'request': 'booking fee adjustment' if decision == 'booking fee override' else decision, 'status': 'check_required', 'action': 'check what can be arranged'},
            EditorialRole.MUST_COMMUNICATE, 'pending_governed_decision_in_current_conversation', priority=4)

    projected_keys: set[str] = set()
    for guide in contract.contextual_guidance:
        projections = normalized_guidance(guide)
        if not projections:
            add('guidance:' + digest([guide.source_reference, guide.client_safe_guidance])[:16], guide.topic,
                {'source_text': guide.client_safe_guidance}, EditorialRole.DEFER,
                'secondary_or_unstructured_guidance_not_needed_now', guide.source_reference)
            continue
        for key, topic, value in projections:
            if key in projected_keys:
                continue
            projected_keys.add(key)
            role, reason, priority = EditorialRole.DEFER, 'not_needed_in_current_turn', 50
            if value.get('status') == 'not_supported' and client_acknowledges_restriction(topic, earlier + '\n' + latest) and not asked_again(topic, latest):
                add('fact:' + key, topic, value, EditorialRole.DEFER, 'client_already_acknowledges_restriction', guide.source_reference)
                continue
            if topic in {'audio_playback', 'projection_display', 'microphones', 'other_technical', 'dj_sound_booth'}:
                if topic in current_topics or (topic in requested_topics and not contract.prior_client_drafts):
                    role, reason, priority = EditorialRole.MUST_COMMUNICATE, 'requested_technical_capability', 1
                if value.get('status') == 'not_supported' and topic in requested_topics:
                    role, reason, priority = EditorialRole.MUST_COMMUNICATE, 'material_known_restriction', 0
            elif topic == 'capacity':
                if value.get('status') == 'outside_limits':
                    role, reason, priority = EditorialRole.MUST_COMMUNICATE, 'material_capacity_restriction', 0
                elif 'capacity' in current_topics:
                    role, reason, priority = EditorialRole.MUST_COMMUNICATE, 'client_asks_about_fit', 1
                elif value.get('near_limit'):
                    role, reason, priority = EditorialRole.MUST_COMMUNICATE, 'near_published_capacity_limit', 1
                # Suitability optional on first contact; never numerical boilerplate.
            elif topic == 'catering_kitchen':
                timing_first = bool(contract.open_client_questions) and bool(re.search(r'check the date|what.*need from us', latest, re.I))
                if topic in current_topics and not timing_first and (asked_again(topic, latest) or not contract.prior_client_drafts):
                    role, reason, priority = EditorialRole.MUST_COMMUNICATE, 'current_catering_suitability_question', 1
            elif topic == 'supplier_access':
                if topic in current_topics:
                    role, reason, priority = EditorialRole.MUST_COMMUNICATE, 'one_immediate_access_constraint', 5
            if topic == 'projection_display' and value.get('status') == 'conditional':
                checks = value.get('check_required', [])
                for condition in checks:
                    direct = alias_matches({'compatibility': ('compatibility', 'compatible'), 'adapters': ('adapter', 'adapters'), 'files': ('file', 'files'), 'screenless setup suitability': ('screenless', 'without a screen')}.get(condition, (condition,)), latest)
                    add('condition:projection:' + condition, 'projection_detail', {'check_required': condition, 'status': 'check_required'},
                        EditorialRole.MUST_COMMUNICATE if direct else EditorialRole.DEFER,
                        'explicit_technical_detail_question' if direct else 'secondary_condition_covered_by_practical_setup_check', guide.source_reference, priority=2)
                value = {**value, 'check_required': ['practical projection setup']}
            elif topic == 'audio_playback' and value.get('status') == 'supported':
                value = {'client_fact': {'background_music_playback': True}}
            elif topic == 'other_technical' and value.get('status') == 'conditional':
                aerial = alias_matches(('aerial', 'rig'), latest + '\n' + earlier)
                value = {'action': 'check', 'subject': 'custom aerial rig' if aerial else 'requested custom equipment',
                         'questions': ['can it be installed safely', 'can it be operated safely'],
                         'report_back': True}
            add('fact:' + key, topic, value, role, reason, guide.source_reference, priority=priority, novelty=True)

    # Known restrictions remain mandatory. Internal feasibility summary labels
    # are not client prose; the typed current capability projections carry facts.
    for index, text in enumerate(contract.known_restrictions):
        internal = text.startswith(('Feasibility as requested:', 'Confirmation still required:', 'Hard constraint:'))
        add('restriction:' + text.split(':', 1)[0], 'restriction', {'text': text},
            EditorialRole.INTERNAL_ONLY if internal else EditorialRole.MUST_COMMUNICATE,
            'internal_feasibility_summary' if internal else 'material_governed_restriction', priority=0)

    # Facts support a needed answer but do not rebuild the case summary. The
    # current client message supplies acknowledgement; dates are governed below.
    for index, text in enumerate(contract.confirmed_case_facts):
        add('case_fact:' + text.split(':', 1)[0], text.split(':', 1)[0], {'fact': text}, EditorialRole.DEFER,
            'case_summary_not_needed_for_this_reply')

    for item in contract.resolution_items:
        add('internal:' + item.proposition_key, 'resolution', {'message': item.message, 'owner': item.resolution_owner,
            'status': item.resolution_status}, EditorialRole.INTERNAL_ONLY,
            'ownership_and_workflow_mechanics_stay_local', source=item.proposition_key)
        if item.client_visibility == 'EXTERNAL_PENDING_VISIBLE':
            add('external:' + item.proposition_key, 'external_pending', {'subject': item.message, 'contact_status': item.resolution_status},
                EditorialRole.MUST_COMMUNICATE, 'recorded_external_pending_state', priority=4)

    # Client-visible future next actions never claim contact or resolution. These
    # are derived from existing topic/owner semantics, not copied blocker prose.
    next_topics: list[str] = []
    if 'supplier_access' in current_topics:
        next_topics.extend(logistics)
    if 'facilitator' in current_topics or ('facilitator' in requested_topics and not contract.open_client_questions):
        next_topics.append('requested facilitator availability and format')
    if not contract.open_client_questions and not next_topics and not any(i.included and i.value.get('status') in {'conditional','check_required','pending'} for i in items):
        if any(i.proposition_key.startswith('availability:') for i in contract.resolution_items):
            next_topics.append('requested date and venue availability')
    if next_topics:
        add('next_step', 'next_step', {'action': 'check', 'subjects': next_topics, 'status': 'check_required',
             **({'requested_event_window': [x for x in contract.confirmed_case_facts if x.startswith('Requested active event')]}
                if 'requested date and venue availability' in next_topics else {})},
            EditorialRole.MUST_COMMUNICATE, 'immediate_wnc_owned_next_step', priority=4)

    mandatory = [i for i in items if i.role in {EditorialRole.MUST_ASK, EditorialRole.MUST_COMMUNICATE}]
    # Mandatory answers and questions win over the budget; optional facts lose.
    # Expanded budgets are explicit and audited, never a reason to over-prune.
    budget = max(3 if len(mandatory) <= 3 else 4, len(mandatory))
    reason = 'compound_material_answers_and_client_questions' if len(mandatory) > 4 else 'minimal_substantive_items_optional_guidance_ranked_last'
    remaining = budget - len(mandatory)
    for index in sorted(range(len(items)), key=lambda n: (items[n].priority, items[n].semantic_key)):
        if items[index].role == EditorialRole.HELPFUL_NOW:
            if remaining > 0:
                remaining -= 1
            else:
                items[index] = replace(items[index], role=EditorialRole.DEFER, reason='editorial_budget_reserved_for_required_answers')
    primary = ('client_owned_missing_information',) if contract.open_client_questions else tuple(sorted(current_topics)) or ('respond_to_current_update',)
    return EditorialContentPlan(contract.response_intent.code, primary, tuple(items), budget, reason)
