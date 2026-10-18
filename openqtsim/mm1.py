"""Fast M/M/1 solver based on the FIFO recursion (no SimPy)."""

from scipy import stats
import numpy as np
import pandas as pd
from openqtsim._validation import (
    validate_positive_integer, validate_positive_rate, validate_process,
)
from openqtsim._random import create_random_streams
from openqtsim._statistics import calculate_statistics


class MM1:
    """A simple simulation method for M/M/1 queues. The basic time unit is hours.

    - :meth:`get_IAT_and_ST` draws interarrival and service times from exponential distributions;
    - :meth:`calculate` computes AT, TSB, TSE, TCSS, TCWQ and ITS per arrival;
    - :meth:`get_stats` prints and returns basic statistics of the results.

    Parameters
    ----------
    lam : float
        Arrival rate (customers per hour).
    mu : float
        Service rate (customers per hour).
    nr_arr : int
        Number of customers.
    arrival_seed : int, optional
        Seed of the interarrival time stream (keyword-only).
    service_seed : int, optional
        Seed of the service time stream (keyword-only); must differ from arrival_seed.

    Attributes
    ----------
    lam, mu, nr_arr
        The inputs.
    arrival_rng, service_rng : numpy.random.Generator
        Random generators of the interarrival and service times.

    Raises
    ------
    ValueError
        If an input is invalid.
    """
    def __init__(self, lam, mu, nr_arr, *, arrival_seed=None, service_seed=None):
        validate_positive_rate(lam, "lam")
        validate_positive_rate(mu, "mu")
        validate_positive_integer(nr_arr, "nr_arr")
        self.arrival_rng, self.service_rng = create_random_streams(arrival_seed, service_seed)
        self.lam = lam  # arrivals per hour
        self.mu = mu  # departures per hour
        self.nr_arr = nr_arr  # nr of customers

    def get_IAT_and_ST(self):  # generate list of inter arrival times
        """Draw interarrival and service times from exponential distributions.

        Returns
        -------
        IAT : numpy.ndarray
            ``nr_arr`` interarrival times (hours) with mean 1 / lam.
        ST : numpy.ndarray
            ``nr_arr`` service times (hours) with mean 1 / mu.
        """

        rv_iat = stats.expon(scale=1 / self.lam)
        rv_st = stats.expon(scale=1 / self.mu)

        # generate list of inter arrival times
        IAT = rv_iat.rvs(self.nr_arr, random_state=self.arrival_rng)

        # generate list of service times
        ST = rv_st.rvs(self.nr_arr, random_state=self.service_rng)

        return IAT, ST

    def calculate(self, IAT, ST):
        """Calculate the customer log of a single-server FIFO queue.

        Any interarrival and service times can be given (not only exponential ones), e.g. the
        output of :meth:`get_IAT_and_ST` or a deterministic example.

        Parameters
        ----------
        IAT : array_like
            ``nr_arr`` finite nonnegative interarrival times (hours).
        ST : array_like
            ``nr_arr`` finite nonnegative service times (hours).

        Returns
        -------
        pandas.DataFrame
            One row per customer with the columns ``IAT``, ``ST``, ``AT`` (arrival time), ``TSB``
            (time service begins), ``TSE`` (time service ends), ``TCSS`` (time customer spends in
            the system), ``TCWQ`` (time customer waits in the queue) and ``ITS`` (idle time of the
            server before this customer).

        Raises
        ------
        ValueError
            If IAT or ST is not one-dimensional with ``nr_arr`` valid values.
        """

        for values, name in [(IAT, "IAT"), (ST, "ST")]:
            if np.ndim(values) != 1 or len(values) != self.nr_arr:
                raise ValueError("{} must be a one-dimensional sequence with nr_arr values.".format(name))
            validate_process("D", pd.DataFrame({name: values}), name, name)

        df_cust = pd.DataFrame()
        AT = []
        TSB = []
        TSE = []
        TCSS = []
        TCWQ = []
        ITS = []

        for i in range(len(IAT)):
            # AT
            if i == 0:
                AT.append(IAT[i])  # time starts at 0 and the first arrival arrives at 0 + IAT
            else:
                AT.append(AT[i - 1] + IAT[i])  # next arrivals start at the previous arrival AT[i-1] + IAT

            # TSB
            if i == 0:
                TSB.append(AT[i])  # first arrival the queue is empty so service begins as soon as customer arrives
            else:
                TSB.append(np.max([AT[i], TSE[i - 1]]))

            # TSE
            TSE.append(TSB[i] + ST[i])  # moment service begins plus service time

            # TCSS
            TCSS.append(TSE[i] - AT[i])  # moment of arrival until service ends

            # TCWQ
            TCWQ.append(TSB[i] - AT[i])  # moment of arrival until service begins

            # ITS
            if i == 0:
                ITS.append(IAT[i])  # the server will start idle until the first arrival
            else:
                ITS.append(np.max([AT[i] - TSE[i - 1], 0]))

        # Add lists to dataframe
        df_cust["IAT"] = IAT
        df_cust["ST"] = ST
        df_cust["AT"] = AT
        df_cust["TSB"] = TSB
        df_cust["TSE"] = TSE
        df_cust["TCSS"] = TCSS
        df_cust["TCWQ"] = TCWQ
        df_cust["ITS"] = ITS

        return df_cust

    def get_stats(self, df_cust):
        """Print and return statistics over time 0 through the last completion.

        Parameters
        ----------
        df_cust : pandas.DataFrame
            Customer log from :meth:`calculate`.

        Returns
        -------
        dict
            Statistics of the customer log
            (e.g. ``waiting_factor``, ``Rho_system``, ``P_0``, ``W_s``, ``W_q``, ``IAT`` and ``ST``).
        """

        summary = calculate_statistics(df_cust)
        value = summary["waiting_factor"]
        print('Waiting time over service time: {}'.format(
            "{:.4f}".format(value) if value is not None else "undefined (mean service time is zero)"))
        print('Observation horizon: 0 to {:.4f} hours'.format(summary["observation_end"]))
        print('')

        value = summary["Rho_system"]
        print('Rho: system utilisation: {:.4f}'.format(value))
        print('')

        value = summary["P_0"]
        print('P_0: probability nobody in the system: {:.4f}'.format(value))

        value = summary["W_s"]
        print('W_s: average time spent in the system: {:.4f}'.format(value))

        value = summary["W_q"]
        print('W_q: average time spent in the queue: {:.4f}'.format(value))

        value = summary["IAT"]
        print('IAT: average inter arrival time: {:.4f}'.format(value))

        value = summary["ST"]
        print('ST: average service time: {:.4f}'.format(value))
        print('')
        return summary
