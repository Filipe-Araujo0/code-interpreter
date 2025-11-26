FROM jupyter/scipy-notebook:latest

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    cmake \
    libboost-all-dev \
    graphviz \
    libgraphviz-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# volta para o usuário padrão do notebook
USER $NB_UID:$NB_GID

# copia o requirements e instala o resto via pip
COPY python_container_requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


# sudo docker build -t code-interpreter-py:latest -f docker/python-exec.Dockerfile .
