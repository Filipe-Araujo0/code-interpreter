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

# switch back to the notebook default user
USER $NB_UID:$NB_GID

# copia o requirements e instala o resto via pip
COPY python_container_requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


# Build the image; otherwise execution fails when the system is called and the image is missing.
# sudo docker build \
#   --label keep=true \
#   -t code-interpreter-py:latest \
#   -f docker/python-exec.Dockerfile \
#   .
# Create a stopped container so this image is not removed during periodic cleanup.
# sudo docker create \
#   --name keep-code-interpreter-py \
#   --label keep=true \
#   code-interpreter-py:latest
