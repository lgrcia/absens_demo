# absens_demo
This project aims to demonstrate the process of aligning images on L1C Sentinel-2 data.

## Steps taken

**Preparation**

I started by reading https://docs.sentinel-hub.com/api/latest/user-guides/beginners-guide/, created a Sentinel Hub account and explored how to request data using the https://services.sentinel-hub.com/api/v1/process API.

**Scoping the project**

I first implemented functions to retrieve the images and started by using the Catalog API to see what images would be available within a date range. I realized I would not need the temporal resolution available (fast-burst of images located around the same datetime) and that it would be easier to pick the least cloudy images on a monthly basis. This would also make for a more interesting visualization as the landscape might display larger changes (buildings being built, seasonal changes, etc.).

*Given all this, I decided that the developed application will allow a user to see a video of aligned monthly images for a given region on Earth.*

As I was retrieving monthly images, I realized that clouds could still be an issue and I experimented (a lot) with evalscript to request the Cloud Mask data in a multipart request (such as [this example](https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l1c/examples/#true-color-and-metadata-multi-part-response-geotiff-and-json))

**Implementation & Methods**

I developed most of the functions in Jupyter notebooks before structuring the code in a Python package.

For the image alignment itself, I followed the guidelines from this [blog post](https://medium.com/sentinel-hub/how-to-co-register-temporal-stacks-of-satellite-images-5167713b3e0b) with two main takeaways:
- Aligning images by comparing the gradient of the mean RGB image (over the RGB bands) works well. I chose a Sobel filter for the edge detection, provided by scikit-image.
- Using Enhanced Cross Correlation is a good solution to find the translation between two images (although in a past interview with EarthCube I found the Harris corner/features detection to work really well)

Before reading these guidelines, I chatted with an LLM that suggested using the B8 band, supposedly less sensitive to atmospheric changes. Eventually I preferred to follow the blog post suggestions.

**Final product**

I decided that the final application would be a simple command line interface, where the user specifies a bounding box (using [Requests Builder](https://apps.sentinel-hub.com/requests-builder/) for example), a start date and the number of month for which to show the area.


**Going further**

Before describing how to install, configure and run this application, here are some ideas to push the project a step further:

*Quality*
- Assess the reliability of the alignment method. For example:
  - Try two methods and check for consistency
  - Develop an independent metric (likely based on cross correlation) to keep track of the alignment results
- Study the robustness of the alignment method:
  - Using the developed metrics, study which bands/metadata combinations lead to the better alignment
  - Also study which pre-processing algorithm (such as edge detection algorithms) lead to the best result

*Infrastructure*
- Implementing a FastAPI to use the function as part of a separate service
- If multiple users were to make requests, from a frontend for example, orchestrate the download and alignment using a workflow management tool (e.g. airflow) for async/scheduled processing

*Performance*
- If performance is a concern, try implementing a multiprocessing approach for the alignment


## Installation

Requires Python 3.10+. Install with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
```

Or with pip:

```bash
pip install .
```

## Configuration

The application requires Sentinel Hub OAuth credentials. Set the following environment variables before running:

```bash
export CLIENT_ID=your_sentinel_hub_client_id
export CLIENT_SECRET=your_sentinel_hub_client_secret
```

You can create OAuth credentials in the [Sentinel Hub Dashboard](https://apps.sentinel-hub.com/dashboard/) under **User Settings > OAuth clients**.

## CLI

The `make_video` command downloads monthly Sentinel-2 imagery for a bounding box, aligns the frames, and produces a GIF.

```
make_video --bbox MIN_LON MIN_LAT MAX_LON MAX_LAT [--start-date YYYY-MM-DD] [--months N] [--folder DIR] [--output FILE]
```

| Argument | Description | Default |
|---|---|---|
| `--bbox` | Bounding box as `min_lon min_lat max_lon max_lat` | required |
| `--start-date` | Start date in `YYYY-MM-DD` format | `2020-01-01` |
| `--months` | Number of months to cover | `30` |
| `--folder` | Directory to store downloaded data | temporary folder |
| `--output` | Output GIF file path | `output.gif` |

**Example** — Toulouse city centre, 12 months starting January 2022:

```bash
make_video --bbox 1.35 43.55 1.50 43.65 --start-date 2022-01-01 --months 12 --output toulouse.gif
```

You can use the [Sentinel Hub Requests Builder](https://apps.sentinel-hub.com/requests-builder/) to find the bounding box coordinates for any area of interest.
