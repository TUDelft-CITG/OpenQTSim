import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import openqtsim
from openqtsim.core import (
    ExtraMetadata, HasArrivalSchedule, HasHandlingTimes, HasLength, HasMaxWait, HasResource, Identifiable,
    create_object, get_all_init_params, inspect_object,
)


@pytest.fixture
def info():
    return pd.DataFrame({
        "name": ["Yellowstar", "ABC", "Oil Trade", "Gen. Cargo Trade", "Fruit Trade", "United"],
        "IAT": [7, 30, 18, 60, 10, 16], "AT": [2, 12, 5, 24, 9, 2],
        "length": [80, 100, 100, 160, 90, 80], "maxwait": [1, 2, 1, 2, 0, 2],
        "unloading": [2, 4, 2, 3, 3, 1], "loading": [1, 3, 0, 1, 3, 4],
        "ST": [3, 7, 2, 4, 6, 5],
    })


@pytest.fixture
def Vessel():
    return create_object("Vessel", (
        Identifiable, HasLength, HasArrivalSchedule, HasHandlingTimes, HasMaxWait, ExtraMetadata))


@pytest.fixture
def Quay():
    return create_object("Quay", (Identifiable, HasResource, HasLength))


def test_mixins_compose_and_store_inputs(Vessel, Quay):
    vessel = Vessel(name="Yellowstar", length=80, AT=2, IAT=7, unloading=2, loading=1, maxwait=1, ST=3)
    assert (vessel.name, vessel.length, vessel.AT, vessel.IAT, vessel.maxwait) == ("Yellowstar", 80, 2, 7, 1)
    assert vessel.service_time == 3 and vessel.metadata == {"ST": 3}
    assert isinstance(vessel.id, str) and vessel.id != Vessel(
        name="Yellowstar", length=80, AT=2, IAT=7, maxwait=1).id
    quay = Quay(name="Quay", nr_resources=2, length=200)
    assert (quay.name, quay.nr_resources, quay.length) == ("Quay", 2, 200)
    assert Quay(name="Quay", length=200).nr_resources == 1


@pytest.mark.parametrize("kwargs", [
    {"name": ""}, {"length": 0}, {"length": np.inf}, {"AT": -1}, {"IAT": 0},
    {"unloading": -1}, {"loading": np.nan}, {"maxwait": -1}, {"maxwait": True},
])
def test_mixins_validate_inputs(Vessel, kwargs):
    data = {"name": "A", "length": 80, "AT": 2, "IAT": 7, "unloading": 2, "loading": 1, "maxwait": 1, **kwargs}
    with pytest.raises(ValueError):
        Vessel(**data)


@pytest.mark.parametrize("nr_resources", [0, 1.5, True])
def test_has_resource_validates_number_of_servers(Quay, nr_resources):
    with pytest.raises(ValueError):
        Quay(name="Quay", nr_resources=nr_resources, length=200)


def test_missing_required_input_and_unknown_input_without_metadata(Quay):
    with pytest.raises(TypeError):
        Quay(name="Quay", nr_resources=2)
    with pytest.raises(TypeError):
        Quay(name="Quay", length=200, colour="grey")


def test_extra_metadata_must_be_last():
    Wrong = create_object("Wrong", (ExtraMetadata, Identifiable))
    with pytest.raises(TypeError, match="last mixin"):
        Wrong(name="A")


def test_create_object_finds_valid_base_order():
    class Base:
        pass

    class Derived(Base):
        pass

    Combined = create_object("Combined", (Base, Derived))
    assert Combined.__mro__[1:3] == (Derived, Base)


def test_inspect_object_reports_required_and_optional_inputs(Vessel, Quay):
    styled, missing = inspect_object(Quay)
    table = styled.data.set_index("parameter")
    assert missing
    assert table.loc["name", "status"] == table.loc["length", "status"] == "missing"
    assert table.loc["nr_resources", "status"] == table.loc["id", "status"] == "optional (unused)"
    assert table.loc["nr_resources", "class"] == "HasResource" and table.loc["nr_resources", "default"] == "1"
    styled, missing = inspect_object(Quay, {"name": "Quay", "length": 200, "nr_resources": 2})
    table = styled.data.set_index("parameter")
    assert not missing
    assert table.loc["name", "status"] == "added" and table.loc["nr_resources", "status"] == "optional (used)"
    assert set(inspect_object(Vessel)[0].data["parameter"]) == get_all_init_params(Vessel) == {
        "name", "id", "length", "AT", "IAT", "unloading", "loading", "maxwait"}


def test_inspect_object_displays_table(monkeypatch, Vessel):
    shown = []
    monkeypatch.setattr("IPython.display.display", shown.append)
    assert inspect_object(Vessel, show_parameter_table=True) is None
    assert len(shown) == 1 and "maxwait" in shown[0].data["parameter"].tolist()


def test_vessel_objects_generate_same_tables_as_info(info, Vessel):
    vessels = [Vessel(**row) for row in info.to_dict("records")]
    for kwargs in [{"nr_arrivals": 20}, {"max_duration_days": 60, "arrival_distribution": "M",
                                         "service_distribution": "M", "arrival_seed": 1, "service_seed": 2}]:
        for expected, actual in zip(openqtsim.generate_vessel_tables(info, **kwargs),
                                    openqtsim.generate_vessel_tables(vessels, **kwargs)):
            assert_frame_equal(expected, actual)


def test_customers_without_length_and_maxwait(info):
    Customer = create_object("Customer", (Identifiable, HasArrivalSchedule, HasHandlingTimes))
    customers = [Customer(name=row["name"], AT=row["AT"], IAT=row["IAT"], unloading=row["unloading"],
                          loading=row["loading"]) for row in info.to_dict("records")]
    arrivals, services = openqtsim.generate_vessel_tables(customers, nr_arrivals=10)
    assert arrivals.columns.tolist() == ["name", "vessel_id", "visit", "IAT", "AT"]
    sim = openqtsim.Simulation(openqtsim.Queue(
        openqtsim.ArrivalProcess("D", arrivals), openqtsim.ServiceProcess("D", services), c=2))
    sim.run(10)
    assert set(sim.return_log()[0].status) == {"served"}


def test_invalid_customer_objects(info, Vessel):
    Named = create_object("Named", (Identifiable,))
    with pytest.raises(ValueError, match="HasArrivalSchedule"):
        openqtsim.generate_vessel_tables([Named(name="A")], nr_arrivals=1)
    Short = create_object("Short", (Identifiable, HasArrivalSchedule, HasHandlingTimes))
    mixed = [Vessel(**info.iloc[0].to_dict()), Short(name="B", AT=1, IAT=2, loading=1)]
    with pytest.raises(ValueError, match="all or none"):
        openqtsim.generate_vessel_tables(mixed, nr_arrivals=2)
    with pytest.raises(ValueError):
        openqtsim.generate_vessel_tables([], nr_arrivals=1)


def test_station_sets_servers_and_quay_length(info, Vessel, Quay):
    quay = Quay(name="Quay", nr_resources=2, length=200)
    arrivals, services = openqtsim.generate_vessel_tables(
        [Vessel(**row) for row in info.to_dict("records")], nr_arrivals=20)

    def log(**kwargs):
        sim = openqtsim.Simulation(openqtsim.Queue(
            openqtsim.ArrivalProcess("D", arrivals), openqtsim.ServiceProcess("D", services), **kwargs))
        sim.run(20)
        return sim.return_log()[0]

    queue = openqtsim.Queue(openqtsim.ArrivalProcess("D", arrivals), openqtsim.ServiceProcess("D", services),
                            station=quay)
    assert (queue.c, queue.quay_length, queue.station) == (2, 200, quay)
    assert_frame_equal(log(station=quay), log(c=2, quay_length=200))
    Berths = create_object("Berths", (Identifiable, HasResource))
    berths = openqtsim.Queue(station=Berths(name="Berths", nr_resources=3))
    assert (berths.c, berths.quay_length, berths.kendall_notation) == (3, None, "M/M/3/inf/inf/FIFO")
    assert openqtsim.Queue().c == 1


def test_station_conflicts_and_mutation_are_rejected(Quay):
    quay = Quay(name="Quay", nr_resources=2, length=200)
    for kwargs in [{"c": 3}, {"quay_length": 150}]:
        with pytest.raises(ValueError, match="conflicts"):
            openqtsim.Queue(station=quay, **kwargs)
    assert openqtsim.Queue(station=quay, c=2, quay_length=200).c == 2
    Named = create_object("Named", (Identifiable,))
    with pytest.raises(ValueError, match="HasResource"):
        openqtsim.Queue(station=Named(name="Quay"))
    sim = openqtsim.Simulation(openqtsim.Queue(station=quay))
    sim.queue.c = 3
    with pytest.raises(ValueError, match="station"):
        sim.run(2)
