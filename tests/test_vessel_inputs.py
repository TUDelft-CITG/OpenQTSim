import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openqtsim import generate_vessel_tables
from openqtsim._random import create_random_streams


@pytest.fixture
def info():
    return pd.DataFrame({
        "name": ["Yellowstar", "ABC", "Oil Trade", "Gen. Cargo Trade", "Fruit Trade", "United"],
        "IAT": [7, 30, 18, 60, 10, 16], "AT": [2, 12, 5, 24, 9, 2],
        "length": [80, 100, 100, 160, 90, 80], "maxwait": [1, 2, 1, 2, 0, 2],
        "unloading": [2, 4, 2, 3, 3, 1], "loading": [1, 3, 0, 1, 3, 4],
        "ST": [999] * 6,
    }, index=[10, 20, 30, 40, 50, 60])


def test_deterministic_twenty_visits_and_conversion(info):
    arrivals, services = generate_vessel_tables(info, nr_arrivals=20)
    assert len(arrivals) == len(services) == 20
    assert list(arrivals.AT / 24) == [2, 2, 5, 9, 9, 12, 16, 18, 19, 23, 23, 24,
                                     29, 30, 34, 37, 39, 41, 42, 44]
    assert list(arrivals.name[:5]) == ["Yellowstar", "United", "Oil Trade", "Yellowstar", "Fruit Trade"]
    np.testing.assert_allclose(arrivals.IAT.cumsum(), arrivals.AT)
    for vessel, visits in arrivals.groupby("vessel_id"):
        row = info.iloc[vessel - 1]
        np.testing.assert_allclose(np.diff(visits.AT), row.IAT * 24)
        np.testing.assert_allclose(services.loc[visits.index, "ST"], (row.loading + row.unloading) * 24)
        assert (visits.maxwait == row.maxwait * 24).all()
        assert (visits.length == row.length).all()
        assert list(visits.visit) == list(range(1, len(visits) + 1))


def test_duration_is_inclusive_and_drives_count(info):
    arrivals, services = generate_vessel_tables(info, max_duration_days=9)
    assert list(arrivals.AT / 24) == [2, 2, 5, 9, 9]
    assert len(services) == 5
    empty_a, empty_s = generate_vessel_tables(info, max_duration_days=1)
    assert empty_a.empty and empty_s.empty
    assert "AT" in empty_a and "ST" in empty_s


@pytest.mark.parametrize("arrival", ["D", "M"])
@pytest.mark.parametrize("service", ["D", "M"])
def test_seeded_reproducibility_and_prefix(info, arrival, service):
    kwargs = dict(arrival_distribution=arrival, service_distribution=service,
                  arrival_seed=42, service_seed=43)
    first_a, first_s = generate_vessel_tables(info, nr_arrivals=30, **kwargs)
    again_a, again_s = generate_vessel_tables(info, nr_arrivals=30, **kwargs)
    assert_frame_equal(first_a, again_a)
    assert_frame_equal(first_s, again_s)
    end = first_a.AT.iloc[-1] / 24 + .01
    duration_a, duration_s = generate_vessel_tables(info, max_duration_days=end, **kwargs)
    assert_frame_equal(first_a, duration_a.iloc[:30])
    assert_frame_equal(first_s, duration_s.iloc[:30])


def test_changing_service_does_not_change_arrivals(info):
    kwargs = dict(nr_arrivals=100, arrival_distribution="M", service_distribution="M",
                  arrival_seed=42)
    a1, s1 = generate_vessel_tables(info, service_seed=43, **kwargs)
    a2, s2 = generate_vessel_tables(info, service_seed=44, **kwargs)
    assert_frame_equal(a1, a2)
    assert not s1.ST.equals(s2.ST)
    deterministic_a, _ = generate_vessel_tables(info, **{**kwargs, "service_distribution": "D"})
    assert_frame_equal(a1, deterministic_a)


def test_stochastic_first_arrival_and_returns_use_separate_means(info):
    single = info.iloc[:1]
    a_rng, s_rng = create_random_streams(42, 43)
    expected = [a_rng.exponential(2)]
    for _ in range(2):
        expected.append(expected[-1] + a_rng.exponential(7))
    arrivals, services = generate_vessel_tables(
        single, nr_arrivals=3, arrival_distribution="M", service_distribution="M",
        arrival_seed=42, service_seed=43)
    np.testing.assert_allclose(arrivals.AT / 24, expected)
    np.testing.assert_allclose(services.ST / 24, s_rng.exponential(3, size=3))


def test_exponential_sample_means(info):
    arrivals, services = generate_vessel_tables(
        info.iloc[:1], nr_arrivals=10000, arrival_distribution="M", service_distribution="M",
        arrival_seed=42, service_seed=43)
    assert (arrivals.IAT.iloc[1:] / 24).mean() == pytest.approx(7, rel=.03)
    assert (services.ST / 24).mean() == pytest.approx(3, rel=.03)


@pytest.mark.parametrize("kwargs", [
    {}, {"nr_arrivals": 20, "max_duration_days": 10}, {"nr_arrivals": 0},
    {"nr_arrivals": True}, {"nr_arrivals": 1.5}, {"max_duration_days": 0},
    {"max_duration_days": np.inf}, {"nr_arrivals": 2, "arrival_distribution": "E2"},
    {"nr_arrivals": 2, "service_distribution": "E2"},
    {"nr_arrivals": 2, "arrival_seed": 42, "service_seed": 42},
])
def test_invalid_configuration(info, kwargs):
    with pytest.raises(ValueError):
        generate_vessel_tables(info, **kwargs)


@pytest.mark.parametrize("column,value", [
    ("IAT", 0), ("IAT", -1), ("AT", -1), ("length", 0), ("maxwait", -1),
    ("loading", np.nan), ("unloading", np.inf), ("AT", True), ("name", ""),
])
def test_invalid_info(info, column, value):
    info[column] = info[column].astype(object)
    info.loc[10, column] = value
    with pytest.raises(ValueError):
        generate_vessel_tables(info, nr_arrivals=20)


def test_zero_first_arrival_and_zero_deterministic_service(info):
    single = info.iloc[:1].copy()
    single["AT"] = single["unloading"] = single["loading"] = 0
    a, s = generate_vessel_tables(single, nr_arrivals=1, arrival_distribution="M")
    assert a.AT.iloc[0] == s.ST.iloc[0] == 0
    with pytest.raises(ValueError, match="exponential service"):
        generate_vessel_tables(single, nr_arrivals=1, service_distribution="M")


def test_missing_columns_and_empty_info(info):
    for invalid in [info.drop(columns="loading"), info.iloc[:0], None]:
        with pytest.raises(ValueError):
            generate_vessel_tables(invalid, nr_arrivals=20)
