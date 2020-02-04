

class Customer:
    """
    Generate customers based on the arrival process.
    """

    def __init__(self, Env, Sim):
        """
        Initialization
        """

        # self.arrival = arrival
        self.Env = Env
        self.Sim = Sim

        Sim.customer_nr += 1
        self.customer_nr = Sim.customer_nr

    def move(self, IAT, AT):
        # IAT and AT have to be administrated when instantiating a customer

        # request access to server
        with self.Env.servers.request() as my_turn:
            yield my_turn

            # determine TSB
            TSB = self.Env.now - self.Env.epoch

            # get ST
            ST = self.Sim.queue.S.get_ST()

            # more time ST forward
            yield self.Env.timeout(ST)

            # determine TSE
            TSE = self.Env.now - self.Env.epoch

            # release server when done
            yield self.Env.servers.release(my_turn)

            # register QL at TSE
            QL = self.Env.servers.data[-1][1]

            self.Sim.log_entry(self.customer_nr, IAT, AT, ST, TSB, TSE, QL)




