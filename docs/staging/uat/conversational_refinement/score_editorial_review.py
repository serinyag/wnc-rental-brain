import json,re,statistics,sys
from pathlib import Path
from collections import Counter
root=Path('/Users/serinya/Documents/WNC Rental Automation');p=root/'docs/staging/uat/conversational_refinement'
slug=sys.argv[1];d=json.loads((p/f'{slug}_results.json').read_text());reviews=json.loads((p/f'{slug}_reviews.json').read_text())
records=[];openings=[];endings=[];structures=[];pricing_sentences=[];capacity_sentences=[]
names=['factual_grounding','wnc_tone','naturalness','clarity','concision','next_step_clarity','operator_confidence']
for s in d['results']:
 for t in s['turns']:
  r=t.get('draft',{}).get('draft_revision')
  if not r:continue
  key=f"{s['scenario_id']}/{t['turn_number']}";review=reviews[key]
  body=r['body_text'];paragraphs=body.split('\n\n');opening=paragraphs[1].split('.')[0] if len(paragraphs)>1 else paragraphs[0];openings.append(opening)
  endings.append(re.split(r'(?<=[.!?])\s+',body)[-1])
  content_paragraphs=[x.strip() for x in paragraphs if x.strip()]
  if content_paragraphs and re.fullmatch(r'(?:Hi|Hello|Dear)\b[^\n]*,',content_paragraphs[0],re.I):content_paragraphs=content_paragraphs[1:]
  structures.append(' / '.join('bullets' if re.search(r'(?m)^\s*[•*-]\s',x) else 'prose' for x in content_paragraphs))
  sentences=re.split(r'(?<!excl\.)(?<!incl\.)(?<=[.!?])\s+','\n\n'.join(content_paragraphs))
  pricing_sentences.extend(x for x in sentences if re.search(r'\b(?:EUR|booking fee|VAT)\b',x,re.I))
  capacity_sentences.extend(x for x in sentences if re.search(r'\b(?:capacity|maximum)\b',x,re.I))
  records.append({'scenario_id':s['scenario_id'],'turn':t['turn_number'],'draft_revision_id':r['inquiry_response_draft_revision_id'],'content_hash':r['content_hash'],'body_word_count':len(body.split()),**review})
texts='\n'.join(t['draft']['draft_revision']['body_text'] for s in d['results'] for t in s['turns'] if t.get('draft',{}).get('draft_revision'))
metrics={'attempted_turns':21,'accepted_drafts':len(records),'turn_coverage_percent':round(100*len(records)/21,2),'grades':dict(Counter(x['grade'] for x in records)),'mean_scores':{k:round(statistics.mean(x['scores'][k] for x in records),2) for k in names},'mean_body_words':round(statistics.mean(x['body_word_count'] for x in records),1),'human_likeness_flags':{k:sum(x['human_review'][k] for x in records) for k in ['unnecessary_information','repeated_information','policy_copy_feel','could_be_materially_shorter']},'human_operator_failures':sum(x['human_review']['human_operator_feel']=='FAIL' for x in records),'editorial_flags':dict(Counter(flag for x in records for flag in x.get('editorial_flags',[]))),'safety_flags':dict(Counter(flag for x in records for flag in x.get('safety_flags',[])))}
variation={'opening_frequency':dict(Counter(openings)),'ending_frequency':dict(Counter(endings)),'phrase_counts':{phrase:len(re.findall(pattern,texts,re.I)) for phrase,pattern in {'I will check':r"I(?:['’]ll| will) check",'I have noted':r"I(?:['’]ve| have) noted",'capacity maximum':r'\bmaximum\b','booking fee':r'\bbooking fee\b'}.items()}}
variation.update({'paragraph_structure_frequency_excluding_salutation':dict(Counter(structures)),'pricing_sentence_frequency':dict(Counter(pricing_sentences)),'capacity_sentence_frequency':dict(Counter(capacity_sentences))})
(p/f'{slug}_assessment.json').write_text(json.dumps({'method':'Direct assistant editorial review of exact synthetic drafts and governed context; independent of the previous numeric grades, no external LLM judge. Flags are subjective editorial assessments; hashes bind reviews to text.','metrics':metrics,'variation':variation,'assessments':records},indent=2,ensure_ascii=False)+'\n')
print(json.dumps(metrics,indent=2))
