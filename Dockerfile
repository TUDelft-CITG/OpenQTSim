# Start with pyramid app image
FROM continuumio/miniconda3

# Install conda stuff first
RUN conda install nomkl pyproj

ADD . /OpenQTSim
WORKDIR /OpenQTSim

# Install the application
RUN pip install -e .