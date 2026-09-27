"""Offline scorer, never used by the request path. None means not applicable/unmeasured."""
from dataclasses import dataclass
from .core import canonical, render

@dataclass(frozen=True)
class EvaluationRecord:
    tool_selection_correct: bool | None
    parameters_correct: bool | None
    numeric_grounding: bool | None
    source_grounding: bool | None
    limitation_present: bool | None
    followup_recalculated: bool | None
    out_of_scope_handled: bool | None
    unsupported_claim: bool | None

def evaluate(query, plan, tool, tool_output, critic, response, *, expected_tool,
             expected_parameters, reference_output, source_ids, out_of_scope=False,
             execution_count_delta=None):
    # query is consumed only for interface compatibility; never retained in usage records.
    if out_of_scope:
        return EvaluationRecord(None,None,None,None,None,None,tool is None and plan.get('out_of_scope') is True and bool(response),None)
    numeric = canonical(tool_output) == canonical(reference_output)
    grounded = bool(tool_output.get('sources')) and all(s.get('source_id') in source_ids for s in tool_output.get('sources', []))
    approved = critic.get('status') in {'PASS','WARN'}
    return EvaluationRecord(tool == expected_tool, canonical(plan['parameters']) == canonical(expected_parameters),
                            numeric, grounded, bool(tool_output.get('limitations')),
                            execution_count_delta >= 2 if plan.get('followup') and execution_count_delta is not None else None,
                            None, not approved or response != render(tool_output))

def kpi(values, definition):
    measured = [v for v in values if v is not None]
    if any(type(v) is not bool for v in measured): raise ValueError('Boolean observations only')
    return {'numerator':sum(measured), 'denominator':len(measured),
            'value':sum(measured)/len(measured) if measured else None, 'definition':definition}
