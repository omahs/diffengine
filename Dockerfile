FROM nvcr.io/nvidia/pytorch:23.07-py3

RUN apt update -y && apt install -y \
    git
RUN apt-get update && apt-get install -y \
    vim \
    libgl1-mesa-dev

# Install python package.
WORKDIR /diffengine
COPY ./ /diffengine
RUN pip install --upgrade pip && \
    pip install --no-cache-dir openmim==0.3.9 && \
    pip install .

# Language settings
ENV LANG C.UTF-8
ENV LANGUAGE en_US

RUN git config --global --add safe.directory /workspace

WORKDIR /workspace
