# Start with pyramid app image
FROM continuumio/miniconda3

ADD . /Queueing-Theory
WORKDIR /Queueing-Theory

# Install the application
RUN pip install -e .

# expose port 80
EXPOSE 8080
# Serve on port 80
CMD queueing serve --port 8080
