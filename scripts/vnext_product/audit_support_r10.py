"""Audit pinned W1 support without replacing its runtime or copying source pages."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def audit(root, support_pin):
    def read(path): return json.loads((root/path).read_bytes())
    h=read('docs/vnext/w1/integration_r10/W1_HANDSHAKE_R10.json')
    refs=h['refs']+[h['status_error_semantics_ref'],h['caller_provenance_ref'],h['capability_descriptor_ref'],h['support_patch']['schema_ref']]
    identities={}
    for ref in refs:
        data=(root/ref['path']).read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        if digest!=ref['sha256'] or len(data)!=ref['bytes']:raise ValueError('Support reference mismatch: '+ref['path'])
        identities[ref['role']]={'path':ref['path'],'sha256':digest,'bytes':len(data)}
    matrix=read('docs/vnext/w1/MOBILITY_ANSWERABILITY_R8.json')
    counts=dict(Counter(c['status'] for c in matrix['capabilities']))
    available=sum(counts.get(s,0) for s in ['AVAILABLE_DIRECT','DERIVABLE_EXACT','ESTIMABLE_WITH_ASSUMPTIONS'])
    a=h['boundaries']['answerability']
    if a['counts_by_status']!=counts or a['available_entry_count']!=available or available!=9 or len(matrix['capabilities'])!=25:raise ValueError('Incorrect availability denominator')
    semantics=read(h['status_error_semantics_ref']['path'])
    unknowns={c['error']['code']:c['user_facing'] for c in semantics['cases'] if c['status']=='unknown'}
    if not {'date_not_validated','invalid_health_snapshot','future_unknown_code'}<=unknowns.keys():raise ValueError('Missing cause-specific/fallback mapping')
    for code in ['invalid_health_snapshot','future_unknown_code']:
        if 'fecha' in unknowns[code].lower():raise ValueError('Invented date cause')
    legacy=next(x for x in h['status_semantics'] if x['status']=='unknown')['meaning']
    return {'classification':'INDEPENDENT_SUPPORT_AUDIT','support_pin':support_pin,'runtime':h['runtime'],
            'refs':identities,'answerability':{'counts_by_status':counts,'available_entries':available,'described_entries':25,'not_tool_count':True},
            'status_error_dispatch':'PASS_CAUSE_SPECIFIC_AND_FALLBACK','unknown_mappings':unknowns,
            'known_support_issue':{'severity':'MEDIUM','owner':'W1','path':'status_semantics[unknown]','legacy_meaning':legacy,
             'mitigation':'Consume status_error_semantics_ref; W3 renders generic evidence insufficiency plus actual error code. Legacy inline array remains date-specific.'},
            'runtime_changed':False,'acceptance':'PASS_WITH_AUTHORITATIVE_ERROR_MAPPING'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--w1-root',type=Path,required=True);p.add_argument('--support-pin',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.w1_root,a.support_pin);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(r['acceptance'])
if __name__=='__main__':main()
