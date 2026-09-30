import math
from pathlib import Path

import pytest

from prototypes.ir_y_volver.walking_r5 import Network, connector_allowed, directions, duration


@pytest.mark.parametrize('metres,expected',[(0,True),(99.9,True),(100,True),(100.1,False)])
def test_connector_boundary(metres,expected):
    assert connector_allowed(metres)==expected


@pytest.mark.parametrize('m,s',[(49.9,180),(50,180),(50.1,240),(99.9,240),(100,240),(100.1,300),(50.00001,240)])
def test_unrounded_duration(m,s):
    assert duration(m)==s


@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1,True])
def test_nonfinite(value):
    with pytest.raises(ValueError): duration(value)
    with pytest.raises(ValueError): connector_allowed(value)
    if value != -1:
        with pytest.raises(ValueError): Network({'a':[value,0]},[],[-1,-1,1,1],'a'*64)


@pytest.mark.parametrize('tags',[
    {'highway':x} for x in ('motorway','motorway_link','trunk','trunk_link','construction','proposed','raceway','steps')
] + [{'highway':'footway',x:y} for x,y in [('foot','no'),('foot','private'),('foot','use_sidepath'),('access','no'),('access','private'),('indoor','yes')]])
def test_restricted_tags(tags):
    assert directions(tags)==()


def network(ways=None):
    return Network({'a':[0,0],'b':[0,0.001],'c':[0,0.002],'d':[0.005,0]},ways or [
        {'id':'1','nodes':['a','b','c'],'tags':{'highway':'footway'}}],[-1,-1,1,1],'a'*64)


def test_direction_and_explicit_permission():
    assert directions({'highway':'footway','access':'private','foot':'yes'})==(1,-1)
    assert directions({'highway':'footway','oneway':'yes'})==(1,-1)
    n=network([{'id':'1','nodes':['a','b','c'],'tags':{'highway':'footway','oneway:foot':'yes'}}])
    assert n.route([0,0],[0,0.002])['status']=='ok'
    assert n.route([0,0.002],[0,0])['reason']=='disconnected_network'


def test_empty_outside_equidistant_disconnected():
    with pytest.raises(ValueError,match='empty_network'): Network({},[],[-1,-1,1,1],'a'*64).nearest([0,0])
    with pytest.raises(ValueError,match='outside_network_bbox'): network().nearest([2,0])
    assert network().nearest([0,0.0005])[0]=='a'
    n=network([{'id':'1','nodes':['a','b'],'tags':{'highway':'footway'}},
               {'id':'2','nodes':['c','d'],'tags':{'highway':'footway'}}])
    assert n.route([0,0],[0,0.002])['reason']=='disconnected_network'


def test_independent_floyd_warshall_and_critical_way():
    n=network(); ids=sorted(n.graph)
    costs={(a,b):0 if a==b else math.inf for a in ids for b in ids}
    for a,edges in n.graph.items():
        for b,length,_ in edges: costs[a,b]=min(costs[a,b],length)
    for k in ids:
        for a in ids:
            for b in ids: costs[a,b]=min(costs[a,b],costs[a,k]+costs[k,b])
    assert n.route(n.nodes['a'],n.nodes['c'])['network_metres']==pytest.approx(costs['a','c'])
    n=network([{'id':'1','nodes':['a','b'],'tags':{'highway':'footway'}},
               {'id':'2','nodes':['c','d'],'tags':{'highway':'footway'}}])
    assert n.route(n.nodes['a'],n.nodes['c'])['status']!='ok'


def test_real_7214_and_geometry_oracle():
    import json
    root=Path(__file__).resolve().parents[2]
    n=Network.from_xml((root/'datos_originales/movilidad/beasain-network-r4-public.osm').read_bytes())
    s=json.loads((root/'prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json').read_bytes())
    centre=[43.04527740634045,-2.1977014177917447]
    for sid in ('7214','7215','7218','7219'):
        stop=s['stops'][sid]; r=n.route([stop['lat'],stop['lon']],centre)
        if sid=='7214':
            assert r['reason']=='disconnected_network';continue
        # Independent great-circle angular separation via atan2, not production haversine.
        def angular(a,b):
            p,q=map(math.radians,[a[0],b[0]]); dl=math.radians(b[1]-a[1])
            numerator=math.hypot(math.cos(q)*math.sin(dl),math.cos(p)*math.sin(q)-math.sin(p)*math.cos(q)*math.cos(dl))
            denominator=math.sin(p)*math.sin(q)+math.cos(p)*math.cos(q)*math.cos(dl)
            return 6371000*math.atan2(numerator,denominator)
        geometry=r['geometry']; length=sum(angular(a,b) for a,b in zip(geometry,geometry[1:]))
        assert length==pytest.approx(r['total_metres'],abs=0.0001)
        assert sum(angular(a,b) for a,b in zip(geometry[1:-1],geometry[2:-1]))==pytest.approx(r['network_metres'],abs=0.0001)
        assert r['seconds']==math.ceil(length/50)*60+120
        assert r['node_ids'][0]==r['start_node_id'] and r['node_ids'][-1]==r['end_node_id']
        for a,b,w in zip(r['node_ids'],r['node_ids'][1:],r['way_ids']):
            assert w in n.ways and any(edge[0]==b and edge[2]==w for edge in n.graph[a])
        assert max(r['connector_metres'])<=100
