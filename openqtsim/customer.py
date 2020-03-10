

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
        t_req = self.Env.now - self.Env.epoch

        self.Sim.c_q += 1
        self.Sim.t.append(t_req)
        self.Sim.t_c_s.append(self.Sim.c_s)
        self.Sim.t_c_q.append(self.Sim.c_q)

        # self.Sim.system_state = self.Sim.system_state.append({'t': t_req, 'c_s': self.Sim.c_s, 'c_q': self.Sim.c_q},
        #                                                      ignore_index=True)
        server = yield self.Env.servers.get()
        t_yield = self.Env.now - self.Env.epoch

        self.Sim.c_q -= 1
        self.Sim.t.append(t_yield)
        self.Sim.t_c_s.append(self.Sim.c_s)
        self.Sim.t_c_q.append(self.Sim.c_q)

        # self.Sim.system_state = self.Sim.system_state.append({'t': t_yield, 'c_s': self.Sim.c_s, 'c_q': self.Sim.c_q},
        #                                                      ignore_index=True)

        # if t_req != t_yield:
        #     self.Sim.c_q += 1
        #     self.Sim.system_state = self.Sim.system_state.append({'t': t_req, 'c_s': self.Sim.c_s, 'c_q': self.Sim.c_q}, ignore_index=True)
        #     self.Sim.c_q -= 1
        #     self.Sim.system_state = self.Sim.system_state.append({'t': t_yield, 'c_s': self.Sim.c_s, 'c_q': self.Sim.c_q}, ignore_index=True)

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
        self.Sim.t.append(TSE)
        self.Sim.t_c_s.append(self.Sim.c_s)
        self.Sim.t_c_q.append(self.Sim.c_q)
        # self.Sim.system_state = self.Sim.system_state.append({'t': self.Env.now, 'c_s': self.Sim.c_s, 'c_q': self.Sim.c_q}, ignore_index=True)

        # update server_info when server was last active
        self.Env.server_info.update({server.id: {'last_active': self.Env.now}})

        # release server when done
        yield self.Env.servers.put(server)

        self.Sim.log_entry(self.customer_nr, IAT, AT, ST, TSB, TSE, ITS, s_id)
