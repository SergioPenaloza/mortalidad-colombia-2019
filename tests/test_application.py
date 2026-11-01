"""Exercise real Dash HTTP callbacks, including export and an empty selection."""

import csv
from io import StringIO

import pytest

from src.app import app


@pytest.fixture
def client():
    return app.server.test_client()


def callback_request(client, key, inputs, state=None, changed=None):
    spec = app.callback_map[key]
    outputs = spec["output"]
    if isinstance(outputs, list):
        outputs = [{"id": item.component_id, "property": item.component_property} for item in outputs]
    else:
        outputs = {"id": outputs.component_id, "property": outputs.component_property}
    response = client.post("/_dash-update-component", json={
        "output": key, "outputs": outputs, "inputs": inputs,
        "state": state or [], "changedPropIds": changed or ["filter-department.value"],
    })
    assert response.status_code == 200, response.get_data(as_text=True)[:500]
    return response.get_json()["response"]


def filter_inputs(department="all", months=None, sex="all", age="all"):
    return [
        {"id": "filter-department", "property": "value", "value": department},
        {"id": "filter-months", "property": "value", "value": months or []},
        {"id": "filter-sex", "property": "value", "value": sex},
        {"id": "filter-age", "property": "value", "value": age},
    ]


def test_routes_and_bundled_map(client):
    for url in ("/", "/_dash-layout", "/_dash-dependencies", "/assets/style.css", "/assets/geo/world_110m.json"):
        assert client.get(url).status_code == 200
    assert client.get("/health").json == {"status": "ok", "year": 2019, "records": 244355}


def test_live_callback_filters_all_charts(client):
    key = next(key for key in app.callback_map if "metric-total" in key)
    response = callback_request(client, key, filter_inputs(department="11"))
    assert response["metric-total"]["children"] == "38.760"
    assert response["metric-x95"]["children"] == "601"
    assert response["metric-departments"]["children"] == "1"
    assert sum(response["monthly-chart"]["figure"]["data"][0]["y"]) == 38760
    assert sum(response["age-chart"]["figure"]["data"][0]["y"]) == 38760
    assert sum(sum(trace["x"]) for trace in response["sex-chart"]["figure"]["data"]) == 38760
    assert len(response["causes-table"]["children"]) == 10


def test_empty_callback_returns_message_and_empty_charts(client):
    key = next(key for key in app.callback_map if "metric-total" in key)
    response = callback_request(client, key, filter_inputs(department="97", sex="3", age="10"))
    assert response["metric-total"]["children"] == "0"
    assert response["metric-older"]["children"] == "—"
    assert response["empty-notice"]["children"] is not None
    assert response["map-chart"]["figure"]["data"] == []


def test_reset_callback_restores_national_scope(client):
    key = next(key for key in app.callback_map if "filter-department.value" in key)
    response = callback_request(client, key, [{"id": "reset-filters", "property": "n_clicks", "value": 1}], changed=["reset-filters.n_clicks"])
    assert response["filter-department"]["value"] == "all"
    assert response["filter-months"]["value"] == []
    assert response["filter-sex"]["value"] == "all"
    assert response["filter-age"]["value"] == "all"


def test_csv_export_respects_filters_and_preserves_codes(client):
    response = callback_request(client, "download-data.data", [{"id": "download-button", "property": "n_clicks", "value": 1}], filter_inputs("05", [2]), ["download-button.n_clicks"])
    download = response["download-data"]["data"]
    assert download["filename"].endswith(".csv")
    records = list(csv.DictReader(StringIO(download["content"].lstrip("\ufeff")), delimiter=";"))
    assert records
    assert {r["codigo_departamento"] for r in records} == {"05"}
    assert {r["mes"] for r in records} == {"2"}
    assert all(len(r["codigo_dane"]) == 5 for r in records)
