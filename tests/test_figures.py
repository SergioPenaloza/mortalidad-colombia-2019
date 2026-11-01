"""Prevent spherical polygon inversion and empty-state rendering regressions."""

from copy import deepcopy

from src import figures
from src.analytics import Filters, filter_data


def test_map_ring_orientation_preserves_source(dataset):
    original = deepcopy(dataset.geography)
    geometry = figures.plotly_geometry(dataset.geography)
    assert dataset.geography == original
    for feature in geometry["features"]:
        geo = feature["geometry"]
        polygons = [geo["coordinates"]] if geo["type"] == "Polygon" else geo["coordinates"]
        for polygon in polygons:
            for i, ring in enumerate(polygon):
                area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:]))
                assert area <= 0 if i == 0 else area >= 0


def test_map_values_and_context(dataset):
    selected = filter_data(dataset.frame, Filters(department="11"))
    chart = figures.department_map(selected, dataset.geography)
    assert list(chart.data[0].locations) == ["11"]
    assert list(chart.data[0].z) == [38760]
    assert len(chart.data[1].locations) == 32


def test_all_figures_support_empty_selections(dataset):
    empty = dataset.frame.iloc[:0]
    charts = [figures.department_map(empty, dataset.geography), figures.monthly_line(empty),
              figures.violent_cities(empty), figures.lowest_cities(empty),
              figures.sex_by_department(empty), figures.age_histogram(empty)]
    for chart in charts:
        assert len(chart.data) == 0
        assert chart.layout.annotations

