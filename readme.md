# absens_demo

![gif](https://raw.githubusercontent.com/lgrcia/absens_demo_data/refs/heads/main/rome.gif)

This project aims to demonstrate the process of aligning images on L1C Sentinel-2 data.

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

## Steps taken

### Preparation

To prepare this project I started by reading [Sentinel Hub Beginners Guide](https://docs.sentinel-hub.com/api/latest/user-guides/beginners-guide/), created a Sentinel Hub account and explored how to request data using the [Process API](https://docs.sentinel-hub.com/api/latest/reference/#tag/process/operation/process).

### Scoping the project

I first implemented functions to retrieve the images and started by using the [Catalog API](https://docs.sentinel-hub.com/api/latest/reference/#tag/catalog_item_search/operation/postCatalogItemSearch) to see what images would be available within a date range. I realized I would not need the temporal resolution available (fast-burst of images located around the same datetime) and that it would be easier to pick the least cloudy images on a monthly basis. This would also make for a more interesting visualization as the landscape might display larger changes (buildings being built, seasonal changes, etc.).

**Given all this, I decided that the developed application will allow a user to see a video of aligned monthly images for a given region on Earth.**

As I was retrieving monthly images, I realized that clouds could still be an issue and I experimented (a lot) with evalscript to request the Cloud Mask data in a multipart request (such as [this example](https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l1c/examples/#true-color-and-metadata-multi-part-response-geotiff-and-json))

### Implementation & Methods

I developed most of the functions in Jupyter notebooks before structuring the code in a Python package.

For the image alignment itself, I followed the guidelines from this [blog post](https://medium.com/sentinel-hub/how-to-co-register-temporal-stacks-of-satellite-images-5167713b3e0b) with two main takeaways:
- Aligning images by comparing the gradient of the mean RGB image (over the RGB bands) works well. I chose a Sobel filter for the edge detection, provided by scikit-image.
- Using Enhanced Cross Correlation is a good solution to find the translation between two images (although in a past interview with EarthCube I found the Harris corner/features detection to work really well)

Before reading these guidelines, I chatted with an LLM that suggested using the B8 band, supposedly less sensitive to atmospheric changes. Eventually I preferred to follow the blog post suggestions.

### Final product

I decided that the final application would be a simple command line interface, where the user specifies a bounding box (aided by the [Requests Builder](https://apps.sentinel-hub.com/requests-builder/) for example), a start date and the number of month for which to show the area.


### Going further

Before describing how to install, configure and run this application, here are some ideas to push the project a step further:

*Quality*
- Assess the reliability of the alignment method. For example:
  - Try two methods and check for consistency
  - Develop an independent metric (likely based on cross correlation) to keep track of the alignment results
- Study the robustness of the alignment method:
  - Using the developed metrics, study which bands/metadata combinations lead to the better alignment
  - Also study which pre-processing algorithm (such as edge detection algorithms) lead to the best result
  - Use the Cloud Mask data to assess coverage and decide if alignment is worth attempting

*Infrastructure*
- Implementing a FastAPI to use the function as part of a separate service
- If multiple users were to make requests, from a frontend for example, orchestrate the download and alignment using a workflow management tool (e.g. airflow) for async/scheduled processing
- Test using known images and outputs instead of mock data (e.g. `_sinusoidal_image` in `test/test_utils`)
- Release the package on PyPI and implement proper versioning

*Performance*
- If performance is a concern, try implementing a multiprocessing approach for the alignment


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

**Example** — Toulouse city centre, 12 months starting January 2022:

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

## On the use of AI

I used LLMs and agents throughout the project in several ways:

- **Scoping**: I asked an LLM questions about common practices in satellite image co-registration to help define the project scope. When doing so I try verified that any cited sources is real.
- **Code suggestions**
- **Test writing**: I used agents to write tests I formulated with natural language. This introduced me to the standard `unittest.mock` module, which is the kind of learning opportunity I love from working with agents.
- **Docstring generation**: I delegated the writing of Python docstrings across package modules to agents.
- **Refactoring**: I used agents extensively to reshape dev scripts into a well-structured Python package. Years of doing this manually allowed me to be very precise about the target structure (see my other Python packages).
- **Improve flow and fix typos**: I often ask an LLM to improve the flow and fix the typos of my sentences, while trying to stay close to my own wording.

In every case, I reviewed and validated the generated code manually before accepting it.

## Final words

Technically I assume there are better ways to treat this problem: better co-registration algorithms, strategies to process images faster... etc. However, with the limited time I had (about half a day), I wanted to focus on showing my capabilities as a software engineer, integrating good practices and being able to rapidly deliver a working solution designed to be maintainable and expandable by others. As a former scientist I know for a fact that these qualities are not so common in a research environment. Hence, I hope this project demonstrates that I am capable of being a key asset in a production environment, bringing along my scientific rigor and motivation to work on demanding state-of-the-art problems. Thanks for proposing this challenge to me!