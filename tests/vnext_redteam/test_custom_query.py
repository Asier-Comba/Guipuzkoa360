"""Custom offline request validation without changing the frozen W1 provider."""

import json

import pytest

from scripts.vnext_product.query_w1_offline import request_from_bytes


VALID = {"origin_id": "zegama_center_stops", "destination_id": "beasain_center_stop_pair",
         "date": "2026-09-29", "appointment_time": "09:30", "duration_minutes": 30}


def encode(value):
    return json.dumps(value).encode("utf-8")


def test_custom_query_accepts_new_allowed_margins():
    request = {**VALID, "arrival_margin_minutes": 15, "boarding_margin_minutes": 8}
    assert request_from_bytes(encode(request)) == request


@pytest.mark.parametrize("change", [
    {"duration_minutes": "30"}, {"duration_minutes": True},
    {"origin_id": None}, {"origin_id": ""}, {"invented_field": 1},
    {"boarding_margin_minutes": 3.5},
])
def test_custom_query_rejects_wrong_shape(change):
    with pytest.raises(ValueError):
        request_from_bytes(encode({**VALID, **change}))


def test_custom_query_rejects_missing_required():
    with pytest.raises(ValueError):
        request_from_bytes(encode({key: value for key, value in VALID.items() if key != "date"}))
