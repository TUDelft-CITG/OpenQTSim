class customer:
    """
    Generate customers based on the arrival process.
    """

    def __init__(self, arrival, environment):
        """
        Initialization
        """

        self.arrival = arrival
        self.environment = environment

    def move(self):
        with self.environment.servers.request() as my_turn:
            yield my_turn

            self.environment.waiting_times.append(self.environment.now - self.arrival)

            self.environment.in_queue -= 1
            self.environment.in_service += 1

            service_time = self.environment.queue.S.service()
            yield self.environment.timeout(service_time)
            self.environment.service_times.append(service_time)

            self.environment.in_service -= 1
            self.environment.system_times.append(self.environment.now - self.arrival)
