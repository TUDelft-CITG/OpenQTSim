"""Top-level package for queueing."""

__author__ = "Joris den Uijl"
__email__ = "jorisdenuijl@gmail.com"
__version__ = "0.1.0"

from .arrival_process import arrival_process
from .service_process import service_process

from .queue import queue
from .customer import customer
from .simulation import simulation
