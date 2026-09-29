"""Independent raw-CSV oracle: no imports from the provider or derived snapshot."""
import csv
import io
import zipfile
from datetime import datetime

ORIGINS={'zegama_center_stops':{'8305','8309'},'segura_herriko_plaza_stops':{'7801','7813'},'idiazabal_center_stops':{'7903','7906'}}
DESTINATION={'7214','7218'}


def read_raw(path):
    with zipfile.ZipFile(path) as z:
        def rows(name):
            if name not in z.namelist():return []
            with z.open(name) as f:return list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig')))
        return {name:rows(name) for name in ('routes.txt','trips.txt','stop_times.txt','calendar.txt','calendar_dates.txt')}


def clock(value):
    parts=list(map(int,value.split(':')))
    if len(parts)==2:parts.append(0)
    return parts[0]*3600+parts[1]*60+parts[2]


def calculate(raw,request):
    d=datetime.strptime(request['date'],'%Y-%m-%d')
    day=d.strftime('%Y%m%d'); weekday=('monday','tuesday','wednesday','thursday','friday','saturday','sunday')[d.weekday()]
    services={r['service_id'] for r in raw['calendar.txt'] if r['start_date']<=day<=r['end_date'] and r[weekday]=='1'}
    for row in raw['calendar_dates.txt']:
        if row['date']==day:
            if row['exception_type']=='1':services.add(row['service_id'])
            else:services.discard(row['service_id'])
    routes={r['route_id'] for r in raw['routes.txt'] if r['route_short_name'].upper()=='GO01'}
    trips={r['trip_id']:r for r in raw['trips.txt'] if r['route_id'] in routes and r['service_id'] in services}
    grouped={key:[] for key in trips}
    for line,row in enumerate(raw['stop_times.txt'],2):
        if row['trip_id'] in grouped:grouped[row['trip_id']].append({**row,'csv_line':line})
    out=[];back=[]
    for rows in grouped.values():
        ordered=sorted(rows,key=lambda r:int(r['stop_sequence']))
        for start in ordered:
            # Explicit CSV ordinary values; never reuse provider predicate.
            if start.get('pickup_type','') not in ('','0'):continue
            for end in ordered:
                if int(end['stop_sequence'])<=int(start['stop_sequence']) or end.get('drop_off_type','') not in ('','0'):continue
                if start['stop_id'] in ORIGINS[request['origin_id']] and end['stop_id'] in DESTINATION:out.append((start,end))
                if start['stop_id'] in DESTINATION and end['stop_id'] in ORIGINS[request['origin_id']]:back.append((start,end))
    appt=clock(request['appointment_time']);duration=request['duration_minutes']*60
    arrival=request.get('arrival_margin_minutes',10)*60;boarding=request.get('boarding_margin_minutes',3)*60
    deadline=clock(request['return_deadline']) if request.get('return_deadline') else 86399
    candidates=[]
    for a,b in out:
        if clock(b['arrival_time'])>appt-arrival or clock(a['departure_time'])<boarding:continue
        for c,e in back:
            if clock(c['departure_time'])<appt+duration+boarding or clock(e['arrival_time'])>deadline:continue
            start=clock(a['departure_time'])-boarding;end=clock(e['arrival_time'])
            candidates.append((end-start,a['trip_id'],c['trip_id'],a,b,c,e))
    if not candidates:return {'status':'no_feasible_journey','total_s':None,'source_rows':[]}
    total,out_id,back_id,*rows=min(candidates,key=lambda x:x[:3])
    return {'status':'ok','total_s':total,'outbound_trip_id':out_id,'return_trip_id':back_id,
            'source_rows':rows,'return_slack_s':clock(rows[2]['departure_time'])-appt-duration-boarding}
