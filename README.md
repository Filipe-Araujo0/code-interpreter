# LibreChat compatible code interpreter

A FastAPI-based code interpreter service that provides code execution and file management capabilities. This service is compatible with the LibreChat Code Interpreter API specification.

> [!NOTE]
> This project is mostly a proof of concept and is not intended to be used in production.   
> 
> For production ready solution and to support the amazing work of LibreChat maintainers use the [LibreChat Code Interpreter](https://code.librechat.ai/pricing).

## Features

- Easy deployment with single docker compose file
- Code is executed in a isolated Docker container sandbox, custom images supported
- Supports file upload and download
- Supports concurrent code execution
- Supports Python and R languages (possibility to extend to other languages)
- RESTful API with OpenAPI documentation

https://github.com/user-attachments/assets/ca74549e-0e32-4659-81a8-158ee9132738

## Usage

### Running the project

Run the project with docker compose using `docker compose -f compose.prod.yml up`

It's possible to overwrite the default environment variables defined in [./app/shared/config.py](./app/shared/config.py) by creating a `.env` file in the root directory.
By default the project will create two directories in the root directory: `./config` and `./uploads`.

`config` directory will hold the sqlite database and temp uploaded files.
`uploads` directory will hold the files uploaded by the users. All files uploaded by the users will be, by default, deleted after 24 hours.

### Changing the port and host paths

By default, the API listens on the port defined by the `PORT` env (see `.env`) and the `HOST_PATH` used for sandbox mounts is derived from the project root.

**Port**

- Edit `.env` in this repo and set:
  ```ini
  PORT=3405  # or any other port
  ```
- Both `compose.yml` (dev) and `compose.prod.yml` (prod) use `${PORT:-8000}` in the `ports` mapping and FastAPI `--port` flag, so changing `PORT` is enough.
- After changing it, restart:
  ```bash
  docker compose down
  docker compose up -d --build
  ```

**Host path / user home**

The code executor launches Docker containers and mounts a host directory into them. For this to work reliably:

- `HOST_PATH` (see `.env` and `app/shared/config.py`) must be the **absolute path to this repo on the host**. For example:
  ```ini
  # If the repo is cloned under /home/alice/code-interpreter
  HOST_PATH=/home/alice/code-interpreter
  HOST_FILE_UPLOAD_PATH=uploads
  ```
- The compose file must mount the repo into the same path inside the container that `HOST_PATH` points to on the host. For example, in `compose.yml`:
  ```yaml
  services:
    code-interpreter:
      env_file:
        - .env
      environment:
        - HOST_PATH=/home/alice/code-interpreter
      volumes:
        - .:/app/
        - .:/home/alice/code-interpreter
        - venv:/app/.venv
        - /var/run/docker.sock:/var/run/docker.sock
  ```
- If you move the repo or run it as another user, update:
  - `HOST_PATH` in `.env` to the new absolute path, and
  - the corresponding `volumes` entry in `compose.yml` (and/or `compose.prod.yml`) so that the same path exists inside the container.

If `HOST_PATH` and the mounted path do not match, the internal Docker executor will fail with errors like `invalid mount config for type "bind": bind source path does not exist`.

### Configuring LibreChat

LibreChat is configured to use the code interpreter API by default.

To configure LibreChat to use the local code interpreter, set the following environment variables in LibreChat:

```ini
LIBRECHAT_CODE_API_KEY=<any-value-here>
LIBRECHAT_CODE_BASEURL=http(s)://host:port/v1/librechat # for local testing use to point to host IP http://host.docker.internal:8000/v1/librechat
```

### Building the execution image with dependencies

The user code runs inside a separate Docker image (`code-interpreter-py:latest` by default). Build it so the required Python libraries are present.

1) (Optional) Edit `python_container_requirements.txt` (or the lighter `python_container_requirements_lite.txt`) to add/remove libs.
2) Build the execution image:
   ```bash
   cd ~/code-interpreter
   docker build -t code-interpreter-py:latest -f docker/python-exec.Dockerfile .
   ```
3) Ensure the API knows which image to use. In `.env` (default already matches):
   ```ini
   PY_CONTAINER_IMAGE=code-interpreter-py:latest
   ```
4) Restart the service (no rebuild of the API layer needed):
   ```bash
   docker compose -f compose.prod.yml up -d
   # or: docker compose up -d   # if you use compose.yml
   ```
5) Quick sanity check that libs are in the image:
   ```bash
   docker run --rm code-interpreter-py:latest python - <<'PY'
   import pandas, numpy
   print("pandas", pandas.__version__)
   print("numpy", numpy.__version__)
   PY
   ```

If you change the requirements file, rebuild the image (step 2) and restart the service (step 4).

### Enabling ODA File Converter (DWG support for ezdxf)

`ezdxf.addons.odafc` requires the ODA File Converter binary. This project supports installing ODA into the execution image at build time via `ODA_DEB_URL`.

1) Download the official Linux `.deb` URL from ODA (after accepting their terms).
2) Set `ODA_DEB_URL` in your `.env`:
   ```ini
   ODA_DEB_URL=https://www.opendesign.com/guestfiles/oda_file_converter/ODAFileConverter_<version>_amd64.deb
   ```
3) Rebuild the execution image:
   ```bash
   docker compose build code-interpreter-py-keeper
   ```
4) Verify inside the image:
   ```bash
   docker run --rm code-interpreter-py:latest sh -lc 'ODAFileConverter --help >/dev/null && echo OK'
   ```

The image defines:
- `ODAFC_EXECUTABLE=/usr/local/bin/odafc-headless`

This wrapper runs ODA via `xvfb-run`, so `ezdxf` can execute in headless/background Linux containers.


## Development

### Installation

1. Install dependencies using uv:
```bash
uv sync --all-extras
source .venv/bin/activate
```

## Running the Application

1. Start the development server:
```bash
docker compose up
```

The API will be available at `http://localhost:8000`. The OpenAPI documentation can be accessed at `http://localhost:8000/docs`.


### Running tests

```bash
pytest
```
