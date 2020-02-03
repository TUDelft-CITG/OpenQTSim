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
        self.arrival_rate = 1.0 / self.arrival_distribution.mean()
        self.mean_arrival_rate = self.arrival_distribution.mean()

    def arrival(self, environment, simulation):
        """
        While the simulation time does not exceed the maximum duration, generate customers
        according to the distribution of the arrival process.
        Each time step is basically a new customer (so time equals customers)
        """

        while True:

            if simulation.max_arrivals < simulation.customer_nr:
                break

            # In the case of a poisson arrival process
            if self.symbol == "M":
                # determine the inter-arrival time and checkout
                IAT = simulation.queue.A.get_IAT()
                yield environment.timeout(IAT)

                # determine the arrival time
                AT = environment.now - environment.epoch

                # Create a customer
                customer_new = customer(environment, simulation)

                # Make the customer go through the system
                environment.process(customer_new.move(IAT, AT))

            elif self.symbol == "D":
                # Draw IAT and ST
                id = simulation.queue.A.arrival_distribution.loc[
                    simulation.customer_nr, ["name"]
                ].item()
                IAT = simulation.queue.A.arrival_distribution.loc[
                    simulation.customer_nr, ["IAT"]
                ].item()
                ST = simulation.queue.S.service_distribution.loc[
                    simulation.customer_nr, ["ST"]
                ].item()

                # Move time one IAT forward
                print(IAT)
                yield environment.timeout(IAT)

                AT = environment.now - environment.epoch

                # Create a customer
                customer_new = customer(environment, simulation, customer_id=id)

                # Make the customer go through the system
                environment.process(customer_new.move(IAT, AT, ST))

    def get_IAT(self):
        """
        Return the service time based on the service time distribution.
        """

        return self.arrival_distribution.rvs()
