import math

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
        self.Sim.log_system_state(AT, self.Sim.c_s, self.Sim.c_q)

        service = self.Sim.queue.S
        assigned_server = None
        if service.symbol == "D" and "s_id" in service.srv_rate.columns:
            assigned_server = service.srv_rate.iloc[self.customer_nr - 1]["s_id"]
        if self.Sim.queue.quay_length is not None or self.Sim.customer_maxwait is not None:
            server = yield self.Env.process(self.Sim.request_server(self.customer_nr, assigned_server))
        elif assigned_server is not None:
            server = yield self.Env.servers.get(lambda server: server.id == assigned_server)
        else:
            server = yield self.Env.servers.get()

        if server is None:
            departure = self.Env.now - self.Env.epoch
            self.Sim.c_q -= 1
            self.Sim.c_s -= 1
            self.Sim.log_system_state(departure, self.Sim.c_s, self.Sim.c_q)
            self.Sim.log_customer_state(
                self.customer_nr, IAT, AT, None, None, None, None, None,
                status="reneged", departure=departure)
            return

        self.Sim.c_q -= 1
        self.Sim.log_system_state(self.Env.now - self.Env.epoch, self.Sim.c_s, self.Sim.c_q)

        # register if the server was idle
        ITS = self.Env.now - self.Env.server_info[server.id]['last_active']

        # register which server was used
        s_id = server.id

        # determine TSB
        TSB = self.Env.now - self.Env.epoch

        # get ST
        ST = self.Sim.queue.S.get_ST(server, customer_nr=self.customer_nr)

        # move time ST forward
        yield self.Env.timeout(ST)

        # determine TSE
        TSE = self.Env.now - self.Env.epoch

        self.Sim.c_s -= 1
        self.Sim.log_system_state(TSE, self.Sim.c_s, self.Sim.c_q)

        # update server_info when server was last active
        self.Env.server_info.update({server.id: {'last_active': self.Env.now}})

        # release server when done
        if self.Sim.queue.quay_length is not None:
            del self.Sim.quay_lengths[server.id]
            self.Sim.quay_occupied = math.fsum(self.Sim.quay_lengths.values())
        yield self.Env.servers.put(server)
        self.Sim.capacity_changed.succeed()
        self.Sim.capacity_changed = self.Env.event()

        # add customer info to log
        self.Sim.log_customer_state(self.customer_nr, IAT, AT, ST, TSB, TSE, ITS, s_id)
