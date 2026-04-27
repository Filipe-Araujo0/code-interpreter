FROM jupyter/scipy-notebook:latest

USER root

ARG ODA_DEB_URL=""

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    cmake \
    libboost-all-dev \
    graphviz \
    libgraphviz-dev \
    pkg-config \
    wkhtmltopdf \
    pandoc \
    texlive-latex-base \
    texlive-latex-recommended \
    lmodern \
    xvfb \
    xauth \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libsm6 \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install ODA File Converter only when URL is provided (license/terms accepted externally).
RUN if [ -n "$ODA_DEB_URL" ]; then \
    wget -O /tmp/odafc.deb "$ODA_DEB_URL" \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/odafc.deb \
    && rm -f /tmp/odafc.deb \
    && rm -rf /var/lib/apt/lists/*; \
    else \
    echo "Skipping ODA File Converter install (ODA_DEB_URL not set)."; \
    fi

# Wrapper used by ezdxf/odafc in headless Linux containers.
RUN printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'if ! command -v ODAFileConverter >/dev/null 2>&1; then' \
    '  echo "ODAFileConverter not found in PATH. Install ODA and rebuild the image." >&2' \
    '  exit 127' \
    'fi' \
    'export QT_QPA_PLATFORM=offscreen' \
    'exec xvfb-run -a ODAFileConverter "$@"' \
    > /usr/local/bin/odafc-headless \
    && chmod +x /usr/local/bin/odafc-headless

ENV ODAFC_EXECUTABLE=/usr/local/bin/odafc-headless

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
# Keep a running container so this image is not removed during periodic cleanup.
# sudo docker run -d \
#   --name keep-code-interpreter-py \
#   --restart unless-stopped \
#   --label keep=true \
#   code-interpreter-py:latest \
#   sleep infinity
