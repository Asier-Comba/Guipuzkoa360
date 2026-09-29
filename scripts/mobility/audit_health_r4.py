"""Record observed centre/network evidence; never invent a walking connector."""
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def audit(raw):
    tree=ET.parse(raw).getroot()
    nodes={x.get('id'):x for x in tree.findall('node')}
    ways=tree.findall('way')
    tags=lambda x:{t.get('k'):t.get('v') for t in x.findall('tag')}
    centres=[w for w in ways if tags(w).get('ref:osakidetza')=='ambulat_beasain']
    if len(centres)!=1: raise ValueError('centre ambiguous or absent')
    centre=centres[0]; refs=[n.get('ref') for n in centre.findall('nd')]
    entrances=[n for n in refs if tags(nodes[n]).get('entrance') in ('yes','main')]
    pedestrian=[]
    excluded=[]
    for w in ways:
        t=tags(w)
        if not t.get('highway'):continue
        if t.get('foot') in ('no','private') or t.get('access') in ('no','private') or t['highway'] in ('motorway','motorway_link','trunk','trunk_link','construction','proposed','steps'):
            excluded.append(w.get('id'));continue
        pedestrian.append(w)
    connections=[{'entrance_node':n,'way_ids':[w.get('id') for w in pedestrian if n in [r.get('ref') for r in w.findall('nd')]]} for n in entrances]
    rows=list(csv.DictReader((ROOT/'datos_preparados/servicios.csv').open(encoding='utf-8')))
    service=next(r for r in rows if r['service_id']=='entityBC631DA5')
    report={
        'classification':'SOURCE_INSPECTION_NOT_COMPLETED_WALKING_ROUTE',
        'ORIGINAL_ARCHIVE':'NOT_AVAILABLE','OSM_ORIGINAL_COMPONENT':'NOT_AVAILABLE',
        'OSM_NEW_ACQUISITION':{'url':'https://api.openstreetmap.org/api/0.6/map?bbox=-2.203,43.041,-2.190,43.052',
            'retrieved_date':'2026-09-29','bytes':Path(raw).stat().st_size,'sha256':hashlib.sha256(Path(raw).read_bytes()).hexdigest(),
            'license':'OpenStreetMap contributors, ODbL 1.0','license_url':'https://www.openstreetmap.org/copyright',
            'nodes':len(nodes),'ways':len(ways),'admissible_highway_ways':len(pedestrian),'excluded_ways':len(excluded)},
        'centre':service,
        'official_confirmation_url':'https://www.osakidetza.euskadi.eus/ambulatorio-de-beasain/centro-salud/webosk00-cercon/es/',
        'official_confirmation_date':'2026-09-29',
        'source_xlsx_sha256':hashlib.sha256((ROOT/'datos_originales/centros-salud.xlsx').read_bytes()).hexdigest(),
        'osm_centre':{'way_id':centre.get('id'),'version':centre.get('version'),'timestamp':centre.get('timestamp'),
            'ref:osakidetza':'ambulat_beasain','node_ids':refs,'entrance_node_ids':entrances,'connections':connections},
        'HEALTH_DESTINATION_GO_NO_GO':'BLOCKED',
        'reason':'No mapped verified entrance connected to admissible pedestrian network' if not any(c['way_ids'] for c in connections) else 'Walking route and bounded GTFS connectors still require validation',
        'walking_seconds':None,
        'next_action':'Obtain a documented entrance and bounded stop-to-network connectors; validate both directions on the observed network. Do not snap across disconnected components.',
        'limitations':['An address/building polygon is not the pedestrian entrance.',
            'No assignments, capacity, appointment availability or universal accessibility inferred.',
            '7214/7218 remain a stop-only destination; neither is promoted to a healthcare access link.',
            'Excluding steps is not wheelchair certification. New OSM acquisition does not recover historical OSM.']}
    out=ROOT/'docs/vnext/w1/HEALTH_DESTINATION_R4.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    # Public reproducible source derivative removes contributor account identifiers.
    for e in tree:
        for key in ('user','uid','changeset'):
            e.attrib.pop(key,None)
        for tag in list(e.findall('tag')):
            if tag.get('k') in ('email','phone','fax') or tag.get('k','').startswith('contact:'):
                e.remove(tag)
    ET.ElementTree(tree).write(ROOT/'datos_originales/movilidad/beasain-network-r4-public.osm',encoding='utf-8',xml_declaration=True)
    print(json.dumps({'health':'BLOCKED','mapped_entrances':len(entrances),'connected_entrances':sum(bool(c['way_ids']) for c in connections)}))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('raw_osm',type=Path);audit(p.parse_args().raw_osm)
