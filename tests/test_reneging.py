import numpy as np
import pandas as pd
import pytest

import openqtsim


def simulate(iat, st, patience, lengths=None, assignments=None, c=2, service_metadata=False):
    arrivals = pd.DataFrame({"IAT": iat})
    services = pd.DataFrame({"ST": st})
    (services if service_metadata else arrivals)["maxwait"] = patience
    if lengths is not None:
        arrivals["length"] = lengths
    if assignments is not None:
        services["s_id"] = assignments
    sim = openqtsim.Simulation(openqtsim.Queue(
        openqtsim.ArrivalProcess("D", arrivals),
        openqtsim.ServiceProcess("D", services),
        c=c, quay_length=200 if lengths is not None else None,
    ))
    sim.run(len(iat))
    log, states = sim.return_log()
    log = log.sort_values("c_id")
    assert len(log) == len(iat)
    assert sim.c_s == sim.c_q == 0
    assert sim.quay_occupied == 0
    assert len(sim.env.servers.items) == c
    assert not sim.quay_admission.queue
    assert not sim.env.servers.get_queue
    assert np.sum(np.diff(states.t) * states.c_q.to_numpy()[:-1]) == pytest.approx(log.TCWQ.sum())
    assert np.sum(np.diff(states.t) * states.c_s.to_numpy()[:-1]) == pytest.approx(log.TCSS.sum())
    return sim, log


def test_length_blocked_head_reneges_and_releases_fifo_gate():
    _, log = simulate([0, 1, 1], [10, 3, 1], [0, 2, 10], [120, 100, 50])
    assert list(log.status) == ["served", "reneged", "served"]
    assert log.iloc[1].departure == 3
    assert log.iloc[1].TCWQ == 2
    assert log.iloc[2].TSB == 3
    assert log.iloc[1][["TSB", "TSE", "ST", "s_id", "ITS"]].isna().all()


def test_non_head_waiter_expires_without_interfering_with_fifo():
    _, log = simulate([0, 1, 1, 1], [10, 2, 7, 1], [0, 20, 1, 20], c=1)
    assert list(log.status) == ["served", "served", "reneged", "served"]
    assert log.iloc[2].departure == 3
    assert log.iloc[3].TSB == 12


@pytest.mark.parametrize("lengths", [None, [160, 80]])
@pytest.mark.parametrize("patience", [0, 4])
def test_service_at_exact_deadline_wins(lengths, patience):
    iat = [0, 5] if patience == 0 else [0, 1]
    _, log = simulate(iat, [5, 2], [0, patience], lengths, c=1)
    assert list(log.status) == ["served", "served"]
    assert log.iloc[1].TSB == 5


def test_zero_patience_allows_immediate_service_but_not_waiting():
    _, log = simulate([0, 0, 0], [5, 2, 1], [0, 0, 0], [100, 100, 100])
    assert list(log.status) == ["served", "served", "reneged"]
    assert log.iloc[2].departure == log.iloc[2].AT == 0


def test_patience_is_only_for_queue_not_service():
    _, log = simulate([0], [10], [1])
    assert log.iloc[0].status == "served"
    assert log.iloc[0].TSE == 10


def test_assigned_server_and_service_table_patience():
    _, log = simulate([0, 1, 0], [5, 2, 1], [0, 1, 10],
                      assignments=[2, 2, 1], service_metadata=True)
    assert list(log.status) == ["served", "reneged", "served"]
    assert log.iloc[2].TSB == 1
    assert log.iloc[2].s_id == 1


def test_statistics_include_reneged_waiting_but_not_fictitious_service():
    sim, _ = simulate([1, 1], [10, 100], [0, 2], c=1)
    stats = sim.get_stats()
    assert stats["served"] == stats["reneged"] == 1
    assert stats["observation_end"] == 11
    assert stats["W_q"] == 1
    assert stats["W_s"] == 6
    assert stats["ST"] == 10
    assert stats["L_q"] == pytest.approx(2 / 11)
    assert stats["L_s"] == pytest.approx(12 / 11)
    assert stats["Rho_server"] == pytest.approx(10 / 11)


def test_several_deadlines_at_same_time_release_fifo_in_order():
    _, log = simulate([0, 1, 0, 0], [10, 2, 7, 1], [0, 1, 1, 1],
                      [120, 100, 100, 50])
    assert list(log.status) == ["served", "reneged", "reneged", "served"]
    assert log.iloc[3].TSB == 2


def test_reneged_customers_never_request_service_time(monkeypatch):
    calls = []
    original = openqtsim.ServiceProcess.get_ST

    def record_service(self, server, customer_nr):
        calls.append(customer_nr)
        return original(self, server, customer_nr=customer_nr)

    monkeypatch.setattr(openqtsim.ServiceProcess, "get_ST", record_service)
    simulate([0, 1, 1], [10, 3, 1], [0, 2, 10], [120, 100, 50])
    assert calls == [1, 3]


def test_quay_example_reneging_times():
    _, log = simulate(
        [2, 0, 3, 4, 0, 3, 4, 2, 1, 4, 0, 1],
        [3, 5, 2, 3, 6, 7, 3, 5, 6, 3, 2, 4],
        [1, 2, 1, 1, 0, 2, 1, 2, 0, 1, 1, 2],
        [80, 80, 100, 80, 90, 100, 80, 80, 90, 80, 100, 160],
    )
    reneged = log[log.status == "reneged"]
    assert list(reneged.c_id) == [11, 12]
    assert list(reneged.departure) == [24, 26]


@pytest.mark.parametrize("value", [-1, np.nan, np.inf, True, "2", None])
def test_invalid_patience_rejected_before_run(value):
    with pytest.raises(ValueError, match="maxwait"):
        simulate([0], [1], [value])
