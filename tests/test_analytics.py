"""Data invariants and edge cases, including independent reference totals."""

import pandas as pd
import pytest

from src.analytics import Filters, age_counts, filter_data, metrics, monthly_counts, municipality_ranking, top_causes
from src.settings import AGE_CODE_TO_GROUP, AGE_GROUPS


def test_complete_age_partition():
    codes = [code for _, _, lo, hi in AGE_GROUPS for code in range(lo, hi + 1)]
    assert codes == list(range(30))
    assert AGE_CODE_TO_GROUP[4] == 0
    assert AGE_CODE_TO_GROUP[5] == 1
    assert AGE_CODE_TO_GROUP[28] == 9
    assert AGE_CODE_TO_GROUP[29] == 10


def test_national_reference_totals(dataset):
    data = dataset.frame
    assert data.deaths.sum() == 244355
    assert data.groupby("sex", observed=True).deaths.sum().to_dict() == {1: 134573, 2: 109689, 3: 93}
    assert metrics(data)["x95"] == 9273
    assert metrics(data)["unknown_age"] == 23
    assert dataset.quality["unmatched_causes"] == {}


def test_every_grouping_conserves_deaths(dataset):
    data = dataset.frame
    assert monthly_counts(data).sum() == 244355
    assert age_counts(data).sum() == 244355
    assert data.groupby("department", observed=True).deaths.sum().sum() == 244355
    assert data.groupby(["department", "sex"], observed=True).deaths.sum().sum() == 244355


def test_month_order_and_known_values(dataset):
    counts = monthly_counts(dataset.frame)
    assert counts.index.tolist() == list(range(1, 13))
    assert counts.loc[2] == 17974
    assert counts.loc[12] == 21678


def test_combined_filters_and_no_mutation(dataset):
    selection = Filters("11", (1, 12), "2", "8")
    data = filter_data(dataset.frame, selection)
    assert not data.empty
    assert set(data.department) == {"11"}
    assert set(data.month) <= {1, 12}
    assert set(data.sex) == {2}
    assert data.age_code.between(20, 24).all()
    assert dataset.frame.deaths.sum() == 244355
    assert monthly_counts(data, selection.months).index.tolist() == [1, 12]


def test_unknown_categories_remain_selectable(dataset):
    unknown_sex = filter_data(dataset.frame, Filters(sex="3"))
    unknown_age = filter_data(dataset.frame, Filters(age_group="10"))
    assert unknown_sex.deaths.sum() == 93
    assert unknown_age.deaths.sum() == 23


def test_x95_ranking_is_not_all_homicides(dataset):
    ranking = municipality_ranking(dataset.frame)
    assert ranking.municipality.tolist() == ["76001", "11001", "05001", "08001", "54001"]
    assert ranking.deaths.tolist() == [971, 601, 428, 260, 206]


def test_positive_municipal_ranking_and_ties(dataset):
    ranking = municipality_ranking(dataset.frame, lowest=True)
    assert len(ranking) == 10
    assert ranking.deaths.tolist() == [1] * 9 + [2]
    assert ranking.municipality.tolist()[:3] == ["13440", "13650", "25095"]
    assert ranking.deaths.sum() == 11
    assert ranking.municipality.is_unique


def test_nonmunicipal_places_excluded_from_rankings():
    frame = pd.DataFrame({
        "municipality": ["01001", "01002", "01003"], "municipality_name": ["A", "B", "C"],
        "department_name": ["D"] * 3, "territory_type": ["Municipio", "Área no municipalizada", "Municipio"],
        "deaths": [2, 1, 0], "is_x95": [True] * 3,
    })
    assert municipality_ranking(frame, lowest=True).municipality.tolist() == ["01001"]


def test_causes_keep_full_code_and_correct_denominator(dataset):
    causes = top_causes(dataset.frame, dataset.causes)
    assert causes.iloc[0].cause == "I219"
    assert causes.iloc[0].deaths == 35088
    assert causes.iloc[0].share == pytest.approx(35088 / 244355)
    assert causes.deaths.is_monotonic_decreasing
    assert causes.cause.is_unique


def test_empty_selection(dataset):
    empty = filter_data(dataset.frame, Filters(department="not-a-code"))
    assert metrics(empty)["total"] == 0
    assert metrics(empty)["older_share"] is None
    assert monthly_counts(empty).sum() == 0
    assert top_causes(empty, dataset.causes).empty
    assert municipality_ranking(empty).empty


def test_geography_has_all_codes_and_actual_polygons(dataset):
    features = dataset.geography["features"]
    assert len(features) == 33
    assert {feature["id"] for feature in features} == set(dataset.frame.department)
    for feature in features:
        assert feature["geometry"]["type"] in {"Polygon", "MultiPolygon"}
        assert feature["geometry"]["coordinates"]
