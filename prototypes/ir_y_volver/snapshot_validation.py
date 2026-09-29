"""Fail-closed validation of a normalized, allowlisted scheduled snapshot."""
import json
import math
import re
from datetime import date


class SnapshotError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise SnapshotError(message)


def strict_loads(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise SnapshotError('nonfinite JSON: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def enum(value, allowed, default=None):
    if value == '':
        require(default is not None, 'missing enum')
        return default
    require(type(value) is int and value in allowed, 'invalid enum')
    return value


def seconds(value):
    require(type(value) is str, 'time must be text')
    match = re.fullmatch(r'(\d{1,2}):([0-5]\d):([0-5]\d)', value)
    require(match is not None, 'invalid GTFS time')
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s


def day(value):
    require(type(value) is str, 'date must be text')
    if re.fullmatch(r'\d{8}', value):
        value = value[:4] + '-' + value[4:6] + '-' + value[6:]
    return date.fromisoformat(value)


def integer(value, minimum=0, maximum=10**8):
    require(type(value) is int and minimum <= value <= maximum, 'invalid integer')


def text(value):
    require(type(value) is str and bool(value.strip()), 'missing text')


def validate(s):
    require(type(s) is dict, 'snapshot root must be object')
    required = {'schema_version','snapshot_id','timezone','coverage','defaults','walking_profiles',
                'origins','destinations','stops','calendar','calendar_dates','trips','sources','limitations','scenario_kind'}
    require(required <= s.keys(), 'missing snapshot keys: ' + str(sorted(required - s.keys())))
    require(s['schema_version'] == '0.2.0', 'snapshot schema mismatch')
    text(s['snapshot_id'])
    require(s['timezone'] == 'Europe/Madrid', 'unsupported timezone')
    require(s['scenario_kind'] == 'stop_only', 'health destination not validated in this release')
    for key in ('coverage','defaults','walking_profiles','origins','destinations','stops'):
        require(type(s[key]) is dict and bool(s[key]), 'invalid ' + key)
    for key in ('calendar','calendar_dates','trips','sources','limitations'):
        require(type(s[key]) is list, 'invalid ' + key)
    require(bool(s['trips']) and bool(s['sources']), 'empty data is not coverage')
    require(all(type(x) is str for x in s['limitations']), 'invalid limitations')
    c = s['coverage']
    start, end = day(c['start_date']), day(c['end_date'])
    require(start <= end, 'inverted coverage')
    require(type(c['validated_dates']) is list and bool(c['validated_dates']), 'no validated dates')
    require(c.get('direct_search_complete') is True, 'coverage not declared complete')
    for d in c['validated_dates']:
        require(start <= day(d) <= end, 'validated date outside coverage')
    defaults = s['defaults']
    integer(defaults['arrival_margin_minutes'], 0, 240)
    integer(defaults['boarding_margin_minutes'], 0, 120)
    require(defaults['walking_profile_id'] == 'stop_only', 'unsupported default profile')
    require(set(s['walking_profiles']) == {'stop_only'}, 'unimplemented walking profile')
    for profile in s['walking_profiles'].values():
        require(type(profile) is dict, 'invalid walking profile')
        text(profile['description']); text(profile['source'])
    for sid, stop in s['stops'].items():
        text(sid); require(type(stop) is dict, 'invalid stop')
        text(stop['name'])
        for key, lo, hi in [('lat',-90,90),('lon',-180,180)]:
            value = stop[key]
            require(type(value) in (int,float) and math.isfinite(value) and lo <= value <= hi, 'invalid coordinate')
    for field, metric in [('origins','access_s_by_stop'),('destinations','walk_s_by_stop')]:
        for key, record in s[field].items():
            text(key); require(type(record) is dict, 'invalid entity'); text(record['name'])
            require(type(record['stop_ids']) is list and bool(record['stop_ids']), 'empty stop ids')
            require(all(type(x) is str and x in s['stops'] for x in record['stop_ids']), 'orphan entity stop')
            require(len(record['stop_ids']) == len(set(record['stop_ids'])), 'duplicate entity stop')
            require(type(record[metric]) is dict and set(record[metric]) == set(record['stop_ids']), 'missing ' + metric)
            for value in record[metric].values():
                require(type(value) is int and value == 0, 'stop_only requires explicit zero; walking is unsupported')
    service_ids = set()
    for row in s['calendar']:
        require(type(row) is dict, 'invalid calendar row'); text(row['service_id'])
        require(row['service_id'] not in service_ids, 'duplicate service')
        service_ids.add(row['service_id'])
        require(day(row['start_date']) <= day(row['end_date']), 'inverted calendar')
        for key in ('monday','tuesday','wednesday','thursday','friday','saturday','sunday'):
            enum(row[key], (0,1))
    seen_exceptions = set()
    for row in s['calendar_dates']:
        require(type(row) is dict, 'invalid exception'); text(row['service_id']); day(row['date'])
        enum(row['exception_type'], (1,2))
        key = (row['service_id'], day(row['date']))
        require(key not in seen_exceptions, 'duplicate calendar exception'); seen_exceptions.add(key)
        if s['calendar']:
            require(row['service_id'] in service_ids, 'orphan exception service')
        else:
            service_ids.add(row['service_id'])
    seen = set()
    for trip in s['trips']:
        require(type(trip) is dict, 'invalid trip')
        text(trip['trip_id']); text(trip['route_id'])
        require(trip['trip_id'] not in seen, 'duplicate trip'); seen.add(trip['trip_id'])
        require(trip['service_id'] in service_ids, 'orphan service')
        require(type(trip['stops']) is list and len(trip['stops']) >= 2, 'insufficient stop times')
        prev_seq, prev_time = -1, -1
        for row in trip['stops']:
            require(type(row) is dict, 'invalid stop time')
            require(row['stop_id'] in s['stops'], 'orphan stop')
            integer(row['sequence']); require(row['sequence'] > prev_seq, 'nonincreasing sequence')
            a, d = seconds(row['arrival']), seconds(row['departure'])
            require(prev_time <= a <= d, 'nonmonotonic times')
            prev_seq, prev_time = row['sequence'], d
            for field in ('pickup_type','drop_off_type'):
                enum(row.get(field, 0), (0,1,2,3), 0)
            # Missing timepoint is exact per GTFS, not an invented approximation.
            enum(row.get('timepoint', 1), (0,1), 1)
    for source in s['sources']:
        require(type(source) is dict, 'invalid source')
        for key in ('source_id','publisher','url','source_sha256','retrieved_date'):
            text(source[key])
        require(source['url'].startswith('https://'), 'invalid source URL')
        require(re.fullmatch('[0-9a-f]{64}',source['source_sha256']) is not None, 'invalid source hash')
        day(source['retrieved_date'])
