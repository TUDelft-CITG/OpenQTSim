import simpy
import pandas as pd
import numpy as np
import datetime
import time
import math
from copy import copy
from scipy import stats
from collections import namedtuple
import seaborn as sns
import matplotlib.pyplot as plt
from openqtsim.queue import Queue
from openqtsim._validation import validate_positive_integer, validate_positive_rate
from openqtsim._random import create_random_streams
from openqtsim._statistics import calculate_statistics


class _PatienceDeadline(simpy.events.Event):
    def __init__(self, env, delay):
        super().__init__(env)
        self._ok = True
        self._value = None
        # Admission and releases at the deadline take precedence over reneging.
        env.schedule(self, priority=2, delay=delay)


class Simulation:
    """
    A discrete event simulation that simulates the queue.
    - queue is a queue based on the queue class
    - arrival_seed and service_seed control separate reproducible random streams
    """

    def __init__(self, queue, max_arr=100, priority=False, *, arrival_seed=None, service_seed=None):
        """
        Initialization (the basic time unit is hours)
        """

        if not isinstance(queue, Queue):
            raise ValueError("queue must be a Queue object.")
        queue.validate()
        validate_positive_integer(max_arr, "max_arr")
        self.arrival_rng, self.service_rng = create_random_streams(arrival_seed, service_seed)
        if not isinstance(priority, (bool, np.bool_)) or priority:
            raise ValueError("priority only supports False; priority queues are not implemented.")

        self.queue = copy(queue)
        self.queue.A = copy(queue.A)
        self.queue.S = copy(queue.S)
        self.max_arr = max_arr

        # set simulation time and epoch
        self.sim_start = datetime.datetime.now()
        self.env = simpy.Environment(initial_time=time.mktime(self.sim_start.timetuple()))
        self.env.epoch = time.mktime(self.sim_start.timetuple())
        self.quay_occupied = 0.0
        self.quay_lengths = {}
        self.quay_admission = simpy.Resource(self.env, capacity=1)
        self.capacity_changed = self.env.event()
        self.customer_lengths = None
        self.customer_maxwait = None

        # initialise counters and logs
        self.c_s = 0  # people in the system
        self.c_q = 0  # people in the queue
        self.system_state = {
            "t": [0],
            "c_s": [0],
            "c_q": [0]}

        self.customer_nr = 0
        self.log = {
            "c_id": [],  # c_id = customer id
            "name": [],
            "length": [],
            "maxwait": [],
            "status": [],
            "departure": [],
            "IAT": [],  # IAT = inter arrival time
            "ST": [],  # ST = service time
            "AT": [],  # AT = now + IAT
            "TSB": [],  # TSB = time service begins
            "TSE": [],  # TSE = time service ends
            "TCSS": [],  # TCSS = time customer spends in the system
            "TCWQ": [],  # TCWQ = time customer waits in the queue
            "ITS": [],  # ITS = idle time of the server
            "s_id": []}  # s_id = server id

        # define arrival and service processes
        if not priority:

            # --- arrival distribution ---
            if self.queue.A.symbol == "M":
                # define the average inter arrival time and add distribution with appropriate scaling
                aver_IAT = 1 / self.queue.A.arr_rate
                self.queue.A.arrival_distribution = stats.expon(scale=aver_IAT)

            elif self.queue.A.symbol[0] == "E":
                # define the average inter arrival time and add distribution with appropriate scaling
                aver_IAT = 1 / self.queue.A.arr_rate
                k = int(self.queue.A.symbol[1:])
                loc = 0
                self.queue.A.arrival_distribution = stats.erlang(k, loc=loc, scale=aver_IAT / k)

            elif self.queue.A.symbol == "D":
                # the deterministic type expects arr_rate to contain a dataframe with columns ["name","IAT","AT"]
                self.queue.A.arrival_distribution = self.queue.A.arr_rate

            if self.queue.A.symbol != "D":
                self.queue.A.arrival_distribution.random_state = self.arrival_rng

            # --- service distribution ---
            self.env.servers = simpy.FilterStore(self.env, capacity=self.queue.c)
            self.env.servers.items = []  # to be filled in the next steps depending on S.symbol
            self.env.server_info = {}  # to be filled in the next steps depending on S.symbol
            Server = namedtuple('Server', 'service_distribution, last_active, id')

            if self.queue.S.symbol == "M":
                # define the average service time and add distribution with appropriate scaling for each server
                aver_ST = 1 / self.queue.S.srv_rate
                for i in range(1, self.queue.c + 1):
                    self.env.servers.items.append(Server(stats.expon(scale=aver_ST), self.env.now, i))
                    self.env.server_info.update({i: {'last_active': self.env.now}})

            elif self.queue.S.symbol[0] == "E":
                # define the average service time and add distribution with appropriate scaling for each server
                aver_ST = 1 / self.queue.S.srv_rate
                for i in range(1, self.queue.c + 1):
                    k = int(self.queue.S.symbol[1:])
                    loc = 0
                    self.env.servers.items.append(Server(stats.erlang(k, loc=loc,  scale=aver_ST/k), self.env.now, i))
                    self.env.server_info.update({i: {'last_active': self.env.now}})

            elif self.queue.S.symbol == "D":
                for i in range(1, self.queue.c + 1):
                    self.env.servers.items.append(Server(self.queue.S.srv_rate, self.env.now, i))
                    self.env.server_info.update({i: {'last_active': self.env.now}})

            if self.queue.S.symbol != "D":
                for server in self.env.servers.items:
                    server.service_distribution.random_state = self.service_rng

        # initiate queue populating process
        self.env.process(self.queue.populate(self.env, self))

    def run(self, max_arr=1000):
        """
        Run simulation
        """

        validate_positive_integer(max_arr, "max_arr")
        self.queue.validate()
        for process, table, column in [
            (self.queue.A, self.queue.A.arr_rate, "IAT"),
            (self.queue.S, self.queue.S.srv_rate, "ST"),
        ]:
            if process.symbol == "D":
                if len(table) < max_arr:
                    raise ValueError("Deterministic '{}' input has {} rows, but {} arrivals were requested.".format(
                        column, len(table), max_arr))

        if self.queue.S.symbol == "D" and "s_id" in self.queue.S.srv_rate.columns:
            assignments = self.queue.S.srv_rate.iloc[:max_arr]["s_id"]
            if not assignments.map(
                lambda value: isinstance(value, (int, float, np.integer, np.floating))
                and not isinstance(value, (bool, np.bool_))
                and np.isfinite(value) and value == int(value)
                and 1 <= value <= self.queue.c
            ).all():
                raise ValueError("Deterministic 's_id' values must identify a server from 1 to {}.".format(
                    self.queue.c))

        self.max_arr = max_arr

        for process, table in [
            (self.queue.A, self.queue.A.arr_rate),
            (self.queue.S, self.queue.S.srv_rate),
        ]:
            if process.symbol == "D" and "maxwait" in table.columns:
                patience = table.iloc[:max_arr]["maxwait"].tolist()
                for value in patience:
                    if (isinstance(value, (bool, np.bool_))
                            or not isinstance(value, (int, float, np.integer, np.floating))
                            or not np.isfinite(value) or value < 0):
                        raise ValueError("Customer maxwait must be a finite non-negative number.")
                self.customer_maxwait = patience
                break

        if self.queue.quay_length is not None:
            table = None
            for process, candidate in [
                (self.queue.A, self.queue.A.arr_rate),
                (self.queue.S, self.queue.S.srv_rate),
            ]:
                if process.symbol == "D" and "length" in candidate.columns:
                    table = candidate
                    break
            if table is None:
                raise ValueError("quay_length requires a 'length' column in a deterministic input table.")
            lengths = table.iloc[:max_arr]["length"].tolist()
            for length in lengths:
                validate_positive_rate(length, "Customer length")
                if length > self.queue.quay_length:
                    raise ValueError("Customer length exceeds quay_length; this vessel can never be served.")
            self.customer_lengths = lengths

        self.env.run()

    def request_server(self, customer_nr, assigned_server):
        """Acquire joint capacity in FIFO order, or leave at the patience deadline."""
        length = self.customer_lengths[customer_nr - 1] if self.customer_lengths is not None else 0
        deadline = None
        if self.customer_maxwait is not None:
            deadline = _PatienceDeadline(self.env, self.customer_maxwait[customer_nr - 1])
        if self.queue.quay_length is None:
            with self.env.servers.get(
                lambda server: assigned_server is None or server.id == assigned_server
            ) as request:
                if deadline is None:
                    yield request
                else:
                    yield request | deadline
                return request.value if request.triggered else None

        with self.quay_admission.request() as request:
            if deadline is None:
                yield request
            else:
                yield request | deadline
                if not request.triggered:
                    return None
            while True:
                available = [
                    server for server in self.env.servers.items
                    if assigned_server is None or server.id == assigned_server
                ]
                required = math.fsum([*self.quay_lengths.values(), length])
                fits = self.queue.quay_length is None or required <= self.queue.quay_length or math.isclose(
                    required, self.queue.quay_length, rel_tol=1e-12, abs_tol=0.0)
                if available and fits:
                    if self.queue.quay_length is not None:
                        self.quay_lengths[available[0].id] = length
                        self.quay_occupied = required
                    server = yield self.env.servers.get(lambda server: server.id == available[0].id)
                    return server
                if deadline is not None and deadline.processed:
                    return None
                if deadline is None:
                    yield self.capacity_changed
                else:
                    yield self.capacity_changed | deadline

    def log_customer_state(self, customer_id, IAT, AT, ST, TSB, TSE, ITS, s_id,
                           *, status="served", departure=None):
        """
        # the following items are logged per customer that enters the system:
        # c = customer id
        # IAT = inter arrival time
        # ST = service time
        # AT = arrival time
        # TSB = time service begins
        # TSE = time service ends
        # TCSS = time customer spends in the system
        # TCWQ = time customer waits in the queue
        # ITS = idle time of the server
        # s_id = id of server assigned to customer
        """

        name = None
        for process, table in [
            (self.queue.A, self.queue.A.arr_rate),
            (self.queue.S, self.queue.S.srv_rate),
        ]:
            if process.symbol == "D" and "name" in table.columns:
                candidate = table.iloc[customer_id - 1]["name"]
                if pd.notna(candidate) and str(candidate).strip():
                    name = candidate
                    break

        self.log["c_id"].append(customer_id)
        self.log["name"].append(name)
        self.log["length"].append(
            self.customer_lengths[customer_id - 1] if self.customer_lengths is not None else None)
        self.log["maxwait"].append(
            self.customer_maxwait[customer_id - 1] if self.customer_maxwait is not None else None)
        self.log["status"].append(status)
        departure = TSE if departure is None else departure
        self.log["departure"].append(departure)
        self.log["IAT"].append(IAT)
        self.log["ST"].append(ST)
        self.log["AT"].append(AT)
        self.log["TSB"].append(TSB)
        self.log["TSE"].append(TSE)
        self.log["TCWQ"].append((departure if status == "reneged" else TSB) - AT)
        self.log["TCSS"].append(departure - AT)
        self.log["ITS"].append(ITS)
        self.log["s_id"].append(s_id)

    def log_system_state(self, t, c_s, c_q):
        """
        # the following items are logged for the state of the system:
        # t = time (from start of simulation)
        # c_s = number of customers in the system
        # c_q = number of customers in the queue
        """

        self.system_state["t"].append(t)
        self.system_state["c_s"].append(c_s)
        self.system_state["c_q"].append(c_q)

    def return_log(self):
        """
        Return the log in the form of a pandas data frame.
        """

        # convert self.log to dataframe
        df_cust = pd.DataFrame.from_dict(self.log)
        df_cust = df_cust.sort_values(by=['AT'], ascending=[True], kind="stable")

        # convert self.system_state to dataframe
        df_sys = pd.DataFrame.from_dict(self.system_state)
        df_sys = df_sys.sort_values(by=['t'], ascending=[True], kind="stable")

        return df_cust, df_sys

    def get_stats(self):
        """
        Print and return statistics over time 0 through the last departure.
        """

        df_cust, _ = self.return_log()
        if len(df_cust) != self.customer_nr:
            raise ValueError("Statistics require all arrived customers to have departed (served or reneged).")
        summary = calculate_statistics(df_cust, self.queue.c)
        if "reneged" in summary:
            print("Departures: {} served, {} reneged".format(summary["served"], summary["reneged"]))

        value = summary["waiting_factor"]
        print('Waiting time in units of service time: {}'.format(
            "{:.4f}".format(value) if value is not None else "undefined (mean service time is zero)"))
        print('Observation horizon: 0 to {:.4f} hours'.format(summary["observation_end"]))
        print('')

        value = summary["Rho_system"]
        print('Rho_system: system utilisation: {:.4f}'.format(value))
        value = summary["Rho_server"]
        print('Rho_server: server utilisation: {:.4f}'.format(value))

        value = summary["P_0"]
        print('P_0: probability nobody in the system: {:.4f}'.format(value))
        print('')

        value = summary["L_s"]
        print('L_s: average nr of customers in the system: {:.4f}'.format(value))
        value = summary["L_q"]

        print('L_q: average nr of customers in the queue: {:.4f}'.format(value))
        value = summary["W_s"]
        print('W_s: average time spent in the system: {:.4f}'.format(value))
        value = summary["W_q"]
        print('W_q: average time spent in the queue: {:.4f}'.format(value))
        print('')

        value = summary["IAT"]
        print('IAT: average inter arrival time: {:.4f}'.format(value))

        value = summary["ST"]
        print('ST: average service time: {:.4f}'.format(value))
        print('')
        return summary

    def plot_system_state(self, fontsize=20):
        """
        Plot number of customers in the system and in the queue as a function of time
        """

        df_cust, df_sys = self.return_log()

        sns.set(style="white", palette="muted", color_codes=True)

        # Set up the matplotlib figure
        fig, ax = plt.subplots(figsize=(14, 7), sharex=True)
        sns.despine(left=True)

        # Plot a simple histogram with binsize determined automatically
        ax.step(df_sys['t'], df_sys['c_s'], where="post", color="b", label="Nr. cust. in system")
        ax.step(df_sys['t'], df_sys['c_q'], where="post", color="r", label="Nr. cust. in queue")
        ax.legend()
        a = b = ax

        # set labels
        a.set_xlabel("Time (hours)", fontsize=fontsize)
        a.set_ylabel("Nr. of customers", fontsize=fontsize)
        a.tick_params(labelsize=fontsize)

        # fig.suptitle(self.queue.kendall_notation, fontsize=fontsize)

        return fig, ax

    def plot_IAT_ST(self, fontsize=20):
        """
        Plot histograms of IAT's and ST's
        """


        df_cust, df_sys = self.return_log()

        sns.set(style="white", palette="muted", color_codes=True)

        # Set up the matplotlib figure
        fig, axes = plt.subplots(1, 2, figsize=(14, 7), sharex=True)
        sns.despine(left=True)

        # Plot a simple histogram with binsize determined automatically
        a = sns.histplot(df_cust['IAT'], kde=False, color="b", ax=axes[0])
        IAT_av = np.mean(df_cust["IAT"])
        # axes[0].plot([IAT_av, IAT_av], [0, axes[0].axis()[-1]], linewidth=3, color='k')
        axes[0].plot([IAT_av, IAT_av], [0, 1000], linewidth=3, color='k')

        b = sns.histplot(df_cust['ST'], kde=False, color="b", ax=axes[1])
        ST_av = np.mean(df_cust["ST"])
        # axes[1].plot([ST_av, ST_av], [0, axes[1].axis()[-1]], linewidth=3, color='k')
        axes[1].plot([ST_av, ST_av], [0, 1000], linewidth=3, color='k')

        # plt.setp(axes, yticks=[])
        plt.tight_layout()

        # set labels
        a.set_xlabel("Inter arrival times", fontsize=fontsize)
        a.set_ylabel("Nr. of customers", fontsize=fontsize)
        a.tick_params(labelsize=fontsize)

        b.set_xlabel("Service times", fontsize=fontsize)
        b.set_ylabel("Nr. of customers", fontsize=fontsize)
        b.tick_params(labelsize=fontsize)

        # fig.suptitle(self.queue.kendall_notation, fontsize=fontsize)

        return fig, axes
