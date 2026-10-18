from openqtsim._validation import validate_process

class ArrivalProcess:
    """
    Arrival process class for use in the OpenQTSim package
    """

    def __init__(self, symbol='M', arr_rate=8):
        """
        symbol: symbol of the process (M, E_k, etc.)
        arr_rate: arrivals per hour
        """

        validate_process(symbol, arr_rate, "arr_rate", "IAT")
        self.symbol = symbol
        self.arr_rate = arr_rate

    def get_IAT(self, customer_nr=[]):
        """
        Return the inter arrival time based on the inter arrival time distribution or deterministic list
        """

        if self.symbol == "M" or self.symbol[0] == "E":
            return self.arrival_distribution.rvs()

        elif self.symbol == "D":
            return self.arrival_distribution.iloc[customer_nr]["IAT"]
