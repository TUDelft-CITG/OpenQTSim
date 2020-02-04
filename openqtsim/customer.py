

class Customer:
    """
    Customer class for use in the OpenQTSim package
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
        """"
        Method to move Customer through the system
        """
        # IAT and AT have to be administrated when instantiating a customer

        # request access to server
        with self.Env.servers.request() as my_turn:
            yield my_turn

            # determine TSB
            TSB = self.Env.now - self.Env.epoch

            # get ST
            ST, customer_id = self.Sim.queue.S.get_ST(self.customer_nr)

            # more time ST forward
            yield self.Env.timeout(ST)

            # determine TSE
            TSE = self.Env.now - self.Env.epoch

            # release server when done
            yield self.Env.servers.release(my_turn)

            # register QL at TSE
            QL = self.Env.servers.data[-1][1]

            self.Sim.log_entry(customer_id, IAT, AT, ST, TSB, TSE, QL)
