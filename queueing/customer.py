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

    def move(self):
        # draw IAT and ST from distributions
        # inter_arrival_time = random.expovariate(self.arrival_rate)
        IAT = self.simulation.queue.A.get_IAT()
        ST = self.simulation.queue.S.get_ST()

        yield self.environment.timeout(IAT)

        # determine AT
        AT = self.environment.now

        # request access to server
        with self.environment.servers.request() as my_turn:
            yield my_turn

            # determine TSB
            TSB = self.environment.now
            yield self.environment.timeout(ST)
            TSE = self.environment.now

            self.simulation.log_entry(IAT, AT, ST, TSB, TSE)

