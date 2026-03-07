# absens_demo

![gif](https://raw.githubusercontent.com/lgrcia/absens_demo_data/refs/heads/main/rome.gif)

This project aims to demonstrate the process of aligning images on L1C Sentinel-2 data.

This project is split in two phases:
- [**Phase 1**](./phase1.md): A simple command line application that retrieves monthly Sentinel-2 images for a given area, aligns them and produces a video. The code is structured in a Python package, with unit tests and documentation.
- [**Phase 2**](./phase2.ipynb): A Jupyter notebook that exploress different metrics to assess the quality of the alignment, and their robustness to different conditions (cloud coverage, noise, etc.). The notebook also contains a discussion of the results and potential improvements.

## Quick test

Without further ado

```bash
mkdir test_absens_demo
cd test_absens_demo
uv venv --python=3.11
source .venv/bin/activate
uv pip install git+https://github.com/lgrcia/absens_demo.git
```
Then create an `.env` file with
```raw
CLIENT_ID=your_sentinel_hub_client_id
CLIENT_SECRET=your_sentinel_hub_client_secret
```
And finally
```bash
uv run --env-file .env make_video --bbox 12.44 41.87 12.54 41.91 --start-date 2022-01-01 --months 24 --output rome.gif
```
`rome.gif` is a gif showing the city of Rome from January 2022 to December 2023, with one frame per month. The images are aligned to show the same area across frames, and the clouds are highlighted in yellow contours.

`make_video` is a CLI application using a well-documented and tested `absens_demo` Python package.

## Installation

Requires Python 3.10+. Install directly from the repository with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv pip install git+https://github.com/lgrcia/absens_demo.git
```

Or clone and install locally:

```bash
git clone https://github.com/lgrcia/absens_demo.git
cd absens_demo
uv sync
```

Or with pip:

```bash
pip install git+https://github.com/lgrcia/absens_demo.git
```

## Configuration

The application requires Sentinel Hub OAuth credentials. Create a `.env` file at the root of the project:

```bash
CLIENT_ID=your_sentinel_hub_client_id
CLIENT_SECRET=your_sentinel_hub_client_secret
```

## CLI

The `make_video` command downloads monthly Sentinel-2 imagery for a bounding box, aligns the frames, and produces a GIF.

```
make_video --bbox MIN_LON MIN_LAT MAX_LON MAX_LAT [--start-date YYYY-MM-DD] [--months N] [--folder DIR] [--output FILE]
```

| Argument       | Description                                       | Default          |
| -------------- | ------------------------------------------------- | ---------------- |
| `--bbox`       | Bounding box as `min_lon min_lat max_lon max_lat` | required         |
| `--start-date` | Start date in `YYYY-MM-DD` format                 | `2020-01-01`     |
| `--months`     | Number of months to cover                         | `30`             |
| `--folder`     | Directory to store downloaded data                | temporary folder |
| `--output`     | Output GIF file path                              | `output.gif`     |

**Example** — Toulouse secret location ;), 12 months starting January 2022:

```bash
uv run  --env-file .env make_video --bbox 1.35 43.55 1.50 43.65 --start-date 2022-01-01 --months 24 --output toulouse.gif
```

**Example** - Rome 
```bash
uv run  --env-file .env make_video --bbox 12.44 41.87 12.52 41.91 --start-date 2022-01-01 --months 24 --output rome.gif
```

You can use the [Sentinel Hub Requests Builder](https://apps.sentinel-hub.com/requests-builder/) to find the bounding box coordinates for any area of interest.


## Highlighted good development practices

In this project I followed several practices to make the development tractable.

- **Semantic commits**: I used the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification, *A specification for adding human and machine readable meaning to commit messages*
- **Comments and Python Docstrings**: All public functions across the package modules are documented with Google-style docstrings. I tried to use inline commnet as much as possible to clarify implementation details
- **Git and Pull Request**: I used git to version control the project and made a pull request I handled on GitHub to merge the development branch into main. This workflow is extremely common for me as the main maintainer and contributor of numerous opens-source Python packages.
- **Unit tests**: I wrote unit tests for some main functions across the package modules. Most of this was done using an LLM agent and reviewed carefully. Overall this development could have benefited more from continuous test writings.
- **Formatting**: I used the black formatter as well as isort
- **CI/CD**: I made a simple CI on GitHub that runs on every pull requests, building and testing the package.
  
## On the use of AI

I used LLMs and agents throughout the project in several ways:

- **Scoping**: I asked an LLM questions about common practices in satellite image co-registration to help define the project scope. When doing so I try verified that any cited sources is real.
- **Code suggestions**
- **Test writing**: I used agents to write tests I formulated with natural language. This introduced me to the standard `unittest.mock` module, which is the kind of learning opportunity I love from working with agents.
- **Docstring generation**: I delegated the writing of Python docstrings across package modules to agents.
- **Refactoring**: I used agents extensively to reshape dev scripts into a well-structured Python package. Years of doing this manually allowed me to be very precise about the target structure (see my other Python packages).
- **Improve flow and fix typos**: I often ask an LLM to improve the flow and fix the typos of my sentences, while trying to stay close to my own wording.

In every case, I reviewed and validated the generated code manually before accepting it.