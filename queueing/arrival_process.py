import random
from scipy import stats

from queueing.customer import customer


class arrival_process:
    """
    Class to represent the arrival process:
    - symbol is the symbol of the process (M, E_k, etc.)
    - scipy.stats probility distribution of arrival times
    """

    def __init__(self, symbol, arrival_distribution):
        """
        Initialization
        """

        self.symbol = symbol
        self.arrival_distribution = arrival_distribution
        self.arrival_rate = 1. / self.arrival_distribution.mean()

    def arrival(self, environment, simulation):
        """
        While the simulation time does not exceed the maximum duration, generate customers
        according to the distribution of the arrival process.
        Each time step is basically a new customer (so time equals customers)
        """

        while True:

            # In the case of a poisson arrival process
            if self.symbol == "M":
                # Make a timestep based on the poisson process
                time = random.expovariate(self.arrival_rate)
                environment.IAT=time
                environment.ST=environment.queue.S.service()
                environment.arrivals.append(time)

                # Create a customer
                customer_new = customer(environment.now, environment)

                environment.in_queue += 1
                environment.process(customer_new.move())

                yield environment.timeout(time)
