

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
        # request access to server
        self.Sim.c_s += 1
        self.Sim.c_q += 1
        t_req = AT
        c_s_req = self.Sim.c_s
        c_q_req = self.Sim.c_q

        server = yield self.Env.servers.get()

        self.Sim.c_q -= 1
        t_yield = self.Env.now - self.Env.epoch
        c_s_yield = self.Sim.c_s
        c_q_yield = self.Sim.c_q

        if t_req != t_yield:  # only log when someone is actually waiting to be served
            self.Sim.log_system_state(t_req, c_s_req, c_q_req)
            self.Sim.log_system_state(t_yield, c_s_yield, c_q_yield)
        else:
            self.Sim.log_system_state(t_yield, c_s_yield, c_q_yield)

        # register if the server was idle
        ITS = self.Env.now - self.Env.server_info[server.id]['last_active']

        # register which server was used
        s_id = server.id

        # determine TSB
        TSB = self.Env.now - self.Env.epoch

        # get ST
        ST = server.service_distribution.rvs()

        # move time ST forward
        yield self.Env.timeout(ST)

        # determine TSE
        TSE = self.Env.now - self.Env.epoch

        self.Sim.c_s -= 1
        if self.Sim.c_q == 0:
            self.Sim.log_system_state(TSE, self.Sim.c_s, self.Sim.c_q)
        # Todo: when a customer leaves the system while somebody is still in the queue, you get a double logging

        # update server_info when server was last active
        self.Env.server_info.update({server.id: {'last_active': self.Env.now}})

        # release server when done
        yield self.Env.servers.put(server)

        # add customer info to log
        self.Sim.log_entry(self.customer_nr, IAT, AT, ST, TSB, TSE, ITS, s_id)
