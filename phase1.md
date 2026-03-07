# Phase 1

## Preparation

To prepare this project I started by reading [Sentinel Hub Beginners Guide](https://docs.sentinel-hub.com/api/latest/user-guides/beginners-guide/), created a Sentinel Hub account and explored how to request data using the [Process API](https://docs.sentinel-hub.com/api/latest/reference/#tag/process/operation/process).

## Scoping the project

I first implemented functions to retrieve the images and started by using the [Catalog API](https://docs.sentinel-hub.com/api/latest/reference/#tag/catalog_item_search/operation/postCatalogItemSearch) to see what images would be available within a date range. I realized I would not need the temporal resolution available (fast-burst of images located around the same datetime) and that it would be easier to pick the least cloudy images on a monthly basis. This would also make for a more interesting visualization as the landscape might display larger changes (buildings being built, seasonal changes, etc.).

**Given all this, I decided that the developed application will allow a user to see a video of aligned monthly images for a given region on Earth.**

As I was retrieving monthly images, I realized that clouds could still be an issue and I experimented (a lot) with evalscript to request the Cloud Mask data in a multipart request (such as [this example](https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l1c/examples/#true-color-and-metadata-multi-part-response-geotiff-and-json))

## Implementation & Methods

I developed most of the functions in Jupyter notebooks before structuring the code in a Python package.

For the image alignment itself, I followed the guidelines from this [blog post](https://medium.com/sentinel-hub/how-to-co-register-temporal-stacks-of-satellite-images-5167713b3e0b) with two main takeaways:
- Aligning images by comparing the gradient of the mean RGB image (over the RGB bands) works well. I chose a Sobel filter for the edge detection, provided by scikit-image.
- Using Enhanced Cross Correlation is a good solution to find the translation between two images (although in a past interview with EarthCube I found the Harris corner/features detection to work really well)

Before reading these guidelines, I chatted with an LLM that suggested using the B8 band, supposedly less sensitive to atmospheric changes. Eventually I preferred to follow the blog post suggestions.

## Final product

I decided that the final application would be a simple command line interface, where the user specifies a bounding box (aided by the [Requests Builder](https://apps.sentinel-hub.com/requests-builder/) for example), a start date and the number of month for which to show the area.


## Going further

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
