"""Offline directed pedestrian model, not an entrance/accessibility certification."""
import hashlib
import heapq
import math
import xml.etree.ElementTree as ET
from collections import Counter

VERSION = 'r5.1'
PROFILE = 'poc_reference_50m_min_plus_120s'
TAGS = ('highway','area','foot','access','oneway','oneway:foot','foot:forward',
        'foot:backward','tunnel','bridge','layer','indoor','crossing','sidewalk','incline')
ADMITTED = {'residential','living_street','service','unclassified','tertiary',
            'secondary','primary','pedestrian','footway','path','cycleway','track'}


def point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError('invalid coordinate')
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in value):
        raise ValueError('nonfinite coordinate')
    if not -90 <= value[0] <= 90 or not -180 <= value[1] <= 180:
        raise ValueError('coordinate out of range')
    return list(value)


def distance(a,b):
    lat1,lon1=map(math.radians,point(a)); lat2,lon2=map(math.radians,point(b))
    h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 12742000*math.asin(math.sqrt(min(1,max(0,h))))


def duration(metres):
    if type(metres) not in (int,float) or not math.isfinite(metres) or metres < 0:
        raise ValueError('invalid metres')
    return math.ceil(metres/50)*60+120


def connector_allowed(metres, threshold=100):
    if any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in (metres,threshold)):
        raise ValueError('invalid connector')
    return metres <= threshold


def directions(tags):
    if tags.get('highway') not in ADMITTED or tags.get('area')=='yes': return ()
    if tags.get('foot') in {'no','private','use_sidepath'}: return ()
    if tags.get('access') in {'no','private'} and tags.get('foot') not in {'yes','designated','permissive'}: return ()
    # Conservatively exclude indoor/unknown pedestrian direction restrictions.
    if tags.get('indoor') not in (None,'no'): return ()
    foot_oneway=tags.get('oneway:foot','no')
    if foot_oneway not in ('yes','1','true','no','0','false','-1'): return ()
    result=[]
    for direction,field in ((1,'foot:forward'),(-1,'foot:backward')):
        if foot_oneway in ('yes','1','true') and direction==-1: continue
        if foot_oneway=='-1' and direction==1: continue
        if tags.get(field) not in (None,'yes','designated','permissive'): continue
        result.append(direction)
    # Vehicle oneway alone does not imply pedestrian oneway.
    return tuple(result)


class Network:
    def __init__(self,nodes,ways,bbox,source_sha256):
        self.nodes={str(k):point(v) for k,v in nodes.items()}
        self.bbox=bbox
        self.source_sha256=source_sha256
        self.ways={}; self.graph={}; self.audit={tag:Counter() for tag in TAGS}
        for way in sorted(ways,key=lambda x:str(x['id'])):
            for tag in TAGS:
                if tag in way['tags']: self.audit[tag][way['tags'][tag]]+=1
            dirs=directions(way['tags'])
            if not dirs: continue
            ids=list(map(str,way['nodes']))
            if any(n not in self.nodes for n in ids): raise ValueError('missing way node')
            self.ways[str(way['id'])]={'nodes':ids,'tags':{k:v for k,v in way['tags'].items() if k in TAGS}}
            for a,b in zip(ids,ids[1:]):
                if a==b: continue
                length=distance(self.nodes[a],self.nodes[b])
                self.graph.setdefault(a,[]);self.graph.setdefault(b,[])
                for direction in dirs:
                    x,y=(a,b) if direction==1 else (b,a)
                    self.graph[x].append((y,length,str(way['id'])))
        for edges in self.graph.values(): edges.sort()

    @classmethod
    def from_xml(cls,raw):
        tree=ET.fromstring(raw); bounds=tree.find('bounds')
        bbox=[float(bounds.get(k)) for k in ('minlat','minlon','maxlat','maxlon')]
        nodes={n.get('id'):[float(n.get('lat')),float(n.get('lon'))] for n in tree.findall('node')}
        ways=[{'id':w.get('id'),'nodes':[n.get('ref') for n in w.findall('nd')],
               'tags':{t.get('k'):t.get('v') for t in w.findall('tag')}} for w in tree.findall('way')]
        return cls(nodes,ways,bbox,hashlib.sha256(raw).hexdigest())

    def nearest(self,coordinate):
        lat,lon=point(coordinate)
        if not self.bbox[0]<=lat<=self.bbox[2] or not self.bbox[1]<=lon<=self.bbox[3]:
            raise ValueError('outside_network_bbox')
        if not self.graph: raise ValueError('empty_network')
        metres,node=min((distance(coordinate,self.nodes[n]),n) for n in self.graph)
        return node,metres

    def route(self,start,end):
        a,ca=self.nearest(start); b,cb=self.nearest(end)
        common={'start_coordinates':point(start),'end_coordinates':point(end),
                'start_node_id':a,'end_node_id':b,'connector_metres':[ca,cb],
                'connector_threshold_m':100,'network_sha256':self.source_sha256,
                'builder_version':VERSION,'walking_profile_id':PROFILE,
                'entrance_verified':False,'modelled_access':True}
        if not connector_allowed(ca) or not connector_allowed(cb):
            return dict(common,status='unknown',reason='connector_over_threshold')
        queue=[(0,a)]; best={a:0}; previous={}
        while queue:
            cost,node=heapq.heappop(queue)
            if cost!=best[node]: continue
            if node==b: break
            for nxt,length,way in self.graph[node]:
                if cost+length < best.get(nxt,math.inf):
                    best[nxt]=cost+length; previous[nxt]=(node,way)
                    heapq.heappush(queue,(cost+length,nxt))
        if b not in best: return dict(common,status='unknown',reason='disconnected_network')
        nodes=[b];ways=[]
        while nodes[-1]!=a:
            prev,way=previous[nodes[-1]];nodes.append(prev);ways.append(way)
        nodes.reverse();ways.reverse()
        total=best[b]+ca+cb
        return dict(common,status='ok',reason=None,node_ids=nodes,way_ids=ways,
                    network_metres=best[b],total_metres=total,seconds=duration(total),
                    geometry=[point(start)]+[self.nodes[n] for n in nodes]+[point(end)],
                    way_tags=[self.ways[w]['tags'] for w in ways])
