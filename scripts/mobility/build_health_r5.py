"""Derive R5 health links from preserved R4 sources. No downloads, no R4 writes."""
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from prototypes.ir_y_volver.walking_r5 import Network, PROFILE

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'prototypes/ir_y_volver'
DOC=ROOT/'docs/vnext/w1'
ID='official-goierrialdea-go01-health-r5-20260929'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def select_centre(records):
    """Priority is explicit and independent of input order; ambiguity cannot vanish."""
    ordered=sorted(records,key=lambda r:(r['priority'],r['source_id']))
    if len({r['priority'] for r in ordered})!=len(ordered): raise ValueError('ambiguous source priority')
    chosen=ordered[0]
    conflict=len({r['address'] for r in ordered})>1
    return {'chosen_source_id':chosen['source_id'],'address':chosen['address'],
            'classification':'conflicting_current_sources' if conflict else 'same_entity_same_site',
            'human_review_required':conflict,'records':ordered,
            'rationale':'Current specific centre page before versioned registry before PADI service listing; no relocation inferred.'}


def build(output=None):
    r4=BASE/'snapshots/official-goierrialdea-go01-r4-20260929.json'
    s=json.loads(r4.read_bytes()); original=ROOT/'datos_originales/movilidad/beasain-network-r4.osm'
    public=ROOT/'datos_originales/movilidad/beasain-network-r4-public.osm'
    expected_original='d70452469ac23b81839417aabda5289f4148d428d2c2b5762347c4f90320a652'
    if original.exists() and sha(original)!=expected_original: raise ValueError('R4 acquisition changed')
    n=Network.from_xml(public.read_bytes())
    health=json.loads((DOC/'HEALTH_DESTINATION_R4.json').read_bytes())
    anchor=[float(health['centre']['latitude']),float(health['centre']['longitude'])]
    records=[{'source_id':'HEALTH_PAGE','priority':1,'address':'Bernedo Enea 1','phone':'943027700'},
             {'source_id':'HEALTH_REGISTRY','priority':2,'address':'Bernedo Enea 1','phone':'943027700'},
             {'source_id':'PADI_2026','priority':3,'address':'Zaldizurreta 2','phone':'943027700'}]
    conflict=select_centre(records)
    sources=[]
    def source(id,role,publisher,url,path,period,transformation,retrieved='2026-09-29'):
        sources.append(dict(source_id=id,source_role=role,publisher=publisher,url=url,
            source_sha256=sha(path),retrieved_date=retrieved,reference_period=period,transformation=transformation))
    source('GTFS','official_schedule','Moveuskadi / Goierrialdea',s['sources'][0]['url'],
           ROOT/'datos_originales/movilidad/goierrialdea-3276fcae.zip','2026-09-28/2026-12-27',
           'R4 normalized GO01 rows, unchanged; approximate stop times, no realtime')
    source('HEALTH_REGISTRY','official_health_registry','Open Data Euskadi',
           'https://opendata.euskadi.eus/catalogo/-/centros-de-salud-publicos-en-euskadi/',
           ROOT/'datos_originales/centros-salud.xlsx','2026-09-20','entityBC631DA5 coordinates EPSG:4326', '2026-09-24')
    source('HEALTH_PAGE','official_health_page','Osakidetza',
           'https://www.osakidetza.euskadi.eus/ambulatorio-de-beasain/webosk00-cercon/es/',
           ROOT/'datos_originales/movilidad/r5/beasain-official.html','Observed 2026-09-29',
           'Specific centre name/address/telephone; publication date not stated')
    source('PADI_2026','official_health_page','Osakidetza',
           'https://www.osakidetza.euskadi.eus/contenidos/informacion/salud_padi/es_def/adjuntos/padi-kontsultak-gipuzkoa.pdf',
           ROOT/'datos_originales/movilidad/r5/padi-2026.pdf','2026-01','Page 4 dental consultation listing; address conflict retained')
    source('OSM','open_network','OpenStreetMap contributors',
           'https://api.openstreetmap.org/api/0.6/map?bbox=-2.203,43.041,-2.190,43.052',
           public,'Acquired 2026-09-29','R4 public derivative removes editor/contact metadata only; ODbL 1.0')
    source('MODEL','model_parameter','GIPUZKOA360',None,BASE/'walking_r5.py','R5.1',
           'ceil(raw total metres/50)*60+120 per complete directed link; each connector <=100 m')
    links={}; candidates=[]
    used_stops={row['stop_id'] for trip in s['trips'] for row in trip['stops']}
    for sid,stop in sorted(s['stops'].items()):
        if sid not in used_stops or not stop['name'].startswith('Beasain -'): continue
        coordinate=[stop['lat'],stop['lon']]; directions={}
        for name,a,b in [('outbound',coordinate,anchor),('return',anchor,coordinate)]:
            try: directions[name]=n.route(a,b)
            except ValueError as exc: directions[name]={'status':'unknown','reason':str(exc)}
        accepted=all(r['status']=='ok' for r in directions.values())
        if accepted:
            for r in directions.values(): r['source_refs']=['GTFS','HEALTH_REGISTRY','OSM','MODEL']
            links[sid]=directions
        candidates.append({'stop_id':sid,'name':stop['name'],'coordinates':coordinate,
                           'included':accepted,'directions':directions})
    limits=['El paseo termina en un punto de referencia modelado del centro; no representa una puerta física verificada.',
            'No puerta-a-puerta, asignación sanitaria, cita disponible ni accesibilidad universal.',
            'Pendientes, cruces, barreras y condiciones temporales no incorporados al tiempo; validar en campo.',
            'Horarios GTFS aproximados programados, no información en tiempo real.',
            'Conflicto de dirección en listado PADI conservado; no se deduce traslado.',
            'Óptimo limitado a paradas y red admitidas; fuera del bbox no implica ausencia de conexión real.']
    evidence={'centre_id':'entityBC631DA5','name':'Ambulatorio de Beasain',
              'centre_identity':'CONFIRMED','centre_anchor':'CONFIRMED_OFFICIAL_POINT',
              'anchor_kind':'official_centre_point','anchor_coordinates':anchor,'crs':'EPSG:4326',
              'address':conflict['address'],'address_conflict':conflict['classification'],
              'human_review_required':True,'modelled_network_access':'PASS' if links else 'FAIL',
              'entrance_verification':'NOT_VERIFIED','entrance_verified':False,'modelled_access':True,
              'door_to_door':'UNAVAILABLE','source_refs':['HEALTH_REGISTRY','HEALTH_PAGE','PADI_2026'],
              'wording':limits[0]}
    payload={'schema_version':'0.3.0','snapshot_id':ID,'scenario_kind':'health_visit',
             'base_snapshot_id':s['snapshot_id'],'base_snapshot_sha256':sha(r4),
             'validated_date':'2026-09-29','destination_id':'beasain_official_centre_anchor',
             'origins':s['origins'],'health_destination':evidence,'walking_links':links,
             'walking_profile_id':PROFILE,'network_sha256':sha(public),
             'osm_acquisition_sha256':expected_original,'sources':sources,'limitations':limits,
             'source_conflict':conflict,'candidates':candidates}
    target=output or BASE/f'snapshots/{ID}.json';dump(target,payload)
    if output is None:
        dump(BASE/'snapshots/allowlist_r5.json',{'schema_version':'0.3.0','snapshot_id':ID,'file':target.name,'sha256':sha(target)})
        node_counts=Counter(); corridor=[]
        used_nodes={node for links_by_direction in links.values() for link in links_by_direction.values() for node in link['node_ids']}
        for node in ET.fromstring(public.read_bytes()).findall('node'):
            tags={t.get('k'):t.get('v') for t in node.findall('tag')}
            relevant={k:v for k,v in tags.items() if k in ('access','barrier','crossing','foot','highway','incline','entrance')}
            for k,v in relevant.items():node_counts[k+'='+v]+=1
            if node.get('id') in used_nodes and relevant:corridor.append({'node_id':node.get('id'),'tags':relevant})
        dump(DOC/'NETWORK_AUDIT_R5.json',{'source_sha256':sha(public),'acquisition_sha256':expected_original,
            'bbox':n.bbox,'nodes':len(n.nodes),'admitted_ways':len(n.ways),'tags':n.audit,'candidates':candidates,
            'node_tag_counts':node_counts,'corridor_node_tags':corridor,
            'policy':'Vehicle oneway does not restrict pedestrians. Explicit foot directions supported. No indoor/steps. Bridge/layer topology retained, no artificial crossings. Incline is not a speed/accessibility model.'})
    return payload


if __name__=='__main__':
    s=build();print(json.dumps({'snapshot':s['snapshot_id'],'included':list(s['walking_links'])}))
