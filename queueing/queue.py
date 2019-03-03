import numpy

class queue:
    """
    Queueing node based on Kendall's notation, in which:
    - A is the arrival process
    - S is the service time distribution
    - c is the number of servers
    - K is the number of places in the system
    - N is the calling population
    - D is the queue discipline
    """
    
    def __init__(self, A, S, c, K = np.inf, N = np.inf, D = "FIFO"):
        """
        Initialization
        """
    
        self.A = A
        self.S = S
        self.c = c
        self.K = K
        self.N = N
        self.D = D
    
    def kendall_notation(self):
        """
        Return queue according to the kendall notation.
        """
        
        return "{}/{}/{}/{}/{}/{}".format(self.A.symbol,
                                          self.S.symbol,
                                          str(self.c),
                                          str(self.K),
                                          str(self.N),
                                          self.D)
    
    def utilization(self, per_server = False):
        """
        The queue utilazation (rho) is equal to arrival rate (lambda)
        multiplied with the mean service time (E(S)).
        
        If the utilization is larger than c the queue length will explode,
        become infinitely long.
        
        If per_server is True, the utilization per server will be returned.
        """
        
        utilization = self.A.arrival_rate * self.S.mean_service_time
        
        if per_server == True:
            return utilization / self.c
        else:
            return utilzation