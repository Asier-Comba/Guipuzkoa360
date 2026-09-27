"""Offline proposal-only evolution and descriptive scenario aggregation."""
from collections import Counter
from dataclasses import asdict, dataclass
from statistics import median

@dataclass(frozen=True)
class QueryPatternRecord:
    normalized_intent: str
    capability: str | None
    success: bool
    failure_category: str | None
    latency_bucket: str
    missing_capability: str | None

@dataclass(frozen=True)
class ImprovementProposal:
    type: str
    evidence: tuple[str, ...]
    frequency: int
    expected_benefit: str
    risk: str
    required_tests: tuple[str, ...]
    rollback: str
    def __post_init__(self):
        if self.type not in {'ALIAS','DATA','METRIC','PROMPT','PERFORMANCE','UX'}:
            raise ValueError('Unknown improvement type')
        if self.frequency < 0: raise ValueError('Negative frequency')

def capability_gaps(patterns, minimum_frequency=3):
    # Only a closed capability vocabulary is retained; arbitrary user text is discarded.
    allowed = {'mobility','capacity','demand','housing','environment'}
    counts = Counter(p.missing_capability for p in patterns if p.missing_capability in allowed)
    return [{'type':'CapabilityGapProposal', 'capability':key, 'frequency':n,
             'status':'REQUIRES_DATA', 'automatic_implementation':False}
            for key,n in sorted(counts.items()) if n >= minimum_frequency]

def geometric_effect(output):
    """Aggregate EXISTING scenario differences; median over distance-changing municipalities."""
    if output.get('status') != 'ok' or 'scenario' not in output:
        raise ValueError('Validated scenario required')
    action = output['scenario']['changed_parameters']['action']
    if action not in {'add_service','remove_service'}: raise ValueError('Add/remove only')
    differences = [r['difference_absolute_m'] for r in output['data'] if r['difference_absolute_m'] != 0]
    values = [-v if action == 'add_service' else v for v in differences]
    if any(v < 0 for v in values): raise ValueError('Contradictory directional effect')
    return {'label':'MARGINAL GEOMETRIC EFFECT' if action == 'add_service' else 'GEOMETRIC SERVICE-REMOVAL SENSITIVITY',
            'affected_municipalities':len(values), 'sum_distance_change_m':round(sum(values),1),
            'median_change_m':median(values) if values else 0, 'max_change_m':max(values,default=0),
            'threshold_transitions':sum(r['baseline_within_threshold'] != r['scenario_within_threshold'] for r in output['data']),
            'denominator':'Municipalities with non-zero distance difference; equal unweighted municipalities.',
            'direction':'reduction' if action == 'add_service' else 'increase',
            'limitations':['Geometric distance only, rounded core differences; no population weighting.',
                           'Not social benefit, health improvement, resilience or an optimal location.']}
