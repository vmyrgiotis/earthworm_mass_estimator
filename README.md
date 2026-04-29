# Earthworm Mass Estimator

A Streamlit app to estimate earthworm area (and, soon, mass) from photos. Deployable on Streamlit Cloud.

## Features
- Upload a photo and estimate earthworm mass
- Simple, interactive Streamlit interface

## Usage
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Explore the example_notebook for use locally. Adjust for batch processing existing images.
5. Run the app: `streamlit run streamlit_photo_app.py`

## Deployment
This app is ready for deployment on [Streamlit Cloud](https://streamlit.io/cloud).

## Methodology 

The algorithm is implemented in Python and provided as an application with a browser-based interface built on Streamlit Community Cloud. The algorithm performs a semi-automated image-based estimation of earthworm mass. The user uploads a photograph of an individual earthworm and interacts only with the controls exposed in the web interface, while all subsequent image-processing and mass-estimation steps are executed automatically by the underlying code.

Methodologically, the tool treats the user-defined region of interest as the primary input to a sequence of basic computer-vision operations. Within this region, the image is analysed to derive geometric descriptors of the worm’s body, such as an effective length and cross-sectional extent (or projected area), obtained from the distribution of worm pixels relative to the background. These quantities are extracted in pixel units and then transformed into physical dimensions using fixed calibration factors embedded in the code, ensuring that uncertainty from user interaction is confined to the initial region selection rather than the scaling procedure.

The derived morphometric metrics are then propagated through an empirically calibrated parametric model that links body size to live mass, typically via a simple linear or power-law relationship fitted to independent earthworm measurements. In this framework, the user-adjustable browser inputs determine only which portion of the image is processed, while the Python implementation handles all segmentation, feature extraction, and application of the calibration equation. The app finally presents the estimated mass alongside an overlay of the analysed region on the original image, enabling visual verification that the worm has been correctly isolated and that the geometric assumptions underpinning the mass estimate are reasonable.


## License
See [LICENSE](LICENSE) for details.
