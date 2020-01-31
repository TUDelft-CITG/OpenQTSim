import random

class customer:
    """
    Generate customers based on the arrival process.
    """

    def __init__(self, environment, simulation):
        """
        Initialization
        """

        # self.arrival = arrival
        self.environment = environment
        self.simulation = simulation

        simulation.customer_nr += 1
        self.customer_nr = simulation.customer_nr

    def move(self, IAT, AT, ST):
        # draw IAT and ST from distributions
        # inter_arrival_time = random.expovariate(self.arrival_rate)

        # request access to server
        with self.environment.servers.request() as my_turn:
            yield my_turn

            # determine TSB
            TSB = self.environment.now - self.environment.epoch
            yield self.environment.timeout(ST)
            TSE = self.environment.now - self.environment.epoch

            self.simulation.log_entry(self.customer_nr, IAT, AT, ST, TSB, TSE)

