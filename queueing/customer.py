import random


class customer:
    """
    Generate customers based on the arrival process.
    """

    def __init__(self, environment, simulation, customer_id=[]):
        """
        Initialization
        """

        # self.arrival = arrival
        self.environment = environment
        self.simulation = simulation

        simulation.customer_nr += 1
        self.customer_nr = simulation.customer_nr
        if len(customer_id) == 0:
            self.customer_id = simulation.customer_nr
        else:
            self.customer_id = customer_id

    def move(self, IAT, AT):
        """
        Move trough the queue.
        The inter arrival time and service times have been drawn from the specified distributions.
        If the server is busy, time is moved forward until the customer can be served.
        """

        # request access to server
        with self.environment.servers.request() as my_turn:
            yield my_turn

            # determine the time service begins
            TSB = self.environment.now - self.environment.epoch

            # determine the service time and checkout
            ST = self.simulation.queue.S.get_ST()
            yield self.environment.timeout(ST)

            # determine the time service ends
            TSE = self.environment.now - self.environment.epoch

            # determine the queue length
            QL = self.environment.servers.data[-1][1]

            # log results
            self.simulation.log_entry(self.customer_id, IAT, AT, ST, TSB, TSE, QL)
