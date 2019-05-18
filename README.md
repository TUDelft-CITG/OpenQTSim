[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/TUDelft-CITG/Queueing-Theory/blob/master/LICENSE)

[![CircleCI](https://circleci.com/gh/TUDelft-CITG/Queueing-Theory.svg?style=svg&circle-token=fe7b8b4d1c30d69ef17df79ebd9e81c3e4823b7e)](https://circleci.com/gh/TUDelft-CITG/Queueing-Theory)
[ ![Coverage](https://oedm.vanoord.com/proxy/circleci_no_redirect/github/TUDelft-CITG/Queueing-Theory/master/latest/f2a7d426bda80a2a2cafbc0d7ac7f5d60e06838e/tmp/artifacts/coverage.svg)](https://oedm.vanoord.com/proxy/circleci_no_redirect/github/TUDelft-CITG/Queueing-Theory/master/latest/f2a7d426bda80a2a2cafbc0d7ac7f5d60e06838e/tmp/artifacts/index.html)
[ ![Documentation](https://img.shields.io/badge/sphinx-documentation-brightgreen.svg)](https://oedm.vanoord.com/proxy/circleci_no_redirect/github/TUDelft-CITG/Queueing-Theory/master/latest/f2a7d426bda80a2a2cafbc0d7ac7f5d60e06838e/tmp/artifacts/docs/index.html)
[ ![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

# Queueing

The queueing packages facilitates discrete event simulation of queues with a Kendall notation.

The following [Kendall notation](https://en.wikipedia.org/wiki/Kendall's_notation) is used, A / S / c / K / N / D, in which:

- A is the arrival process;
- S is the service time distribution;
- c is the number of servers;
- K is the number of places in the system;
- N is the calling population;
- D is the queue discipline.

### Installation

Installation using *pip install queueing* is not yet available. Running following three lines in your command prompt will allow you installing the package as well:

``` bash
# Download the package
git clone https://github.com/TUDelft-CITG/Queueing-Theory

# Go to the correct folder
cd Queueing-Theory

# Install package
pip install -e .
```

### Defining an M/M/1 queue

Once the package is installed a basic M/M/1 queue can be defined with the following 5 lines of python.

``` python
import queueing

# Define arrival process
A = queueing.arrival_process("M", stats.poisson(1 / 0.9))

# Define service time distribution
S = queueing.service_process("M", stats.expon(0))

# Define number of servers
c = 1

# A queue requires A, S and c. K, N and D are initialized as inf/inf/FIFO, which can of course be overwritten.
queue = queueing.queue(A, S, c)
```

### Analytical results of a queue

With a defined queue object basic analytical results can be obtained (if available).

At the moment only analytical results of M/M/c/inf/inf/FIFO are available in the package.

``` python
# The utilization
print(queue.utilization)

# The mean waiting time
print(queue.mean_waiting_time)

# The mean queue length
print(queue.mean_queue_length)
```

### Simulation of a queue

A discrete event simulation can be started by inserting the queue into a simulation object and specifying the simulation duration. The state of the system is logged every second and the results can be obtained with one line of code.

``` python
# Insert queue into simulation object
sim = queueing.simulation(queue)

# Run simulation for 100.000 units of time
sim.simulate(100_000)

# Obtain mean waiting time, mean queue length and more
sim.log
```

### To do

The following should be implemented:

- Define other arrival rates (Erlang, deterministic, etc.);
- Define other queue disciplines;
- Define a network of queues;
- Tag a version 0.1 and upload to pypi.