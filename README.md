# Earthworm Mass Estimator

A Streamlit app to estimate earthworm area (and, soon, mass) from photos. Deployable on Streamlit Cloud.

## Features
- Upload a photo and estimate earthworm mass
- Simple, interactive Streamlit interface

## Methodology 

The algorithm is implemented in Python and provided as an application with a browser-based interface built on Streamlit Community Cloud. It currently performs a semi‑automated, image‑based estimation of earthworm abundance and occupied area on an A4 sheet, with earthworm size‑class grouping and mass estimation to be added in a subsequent version. The user uploads photographs of earthworms placed on an A4 sheet and interacts only with the controls exposed in the web interface, while all subsequent image‑processing steps are executed automatically by the underlying code. An example notebook included in the repository allows users to run the algorithm locally and batch‑process multiple images.

Methodologically, the tool applies a sequence of basic computer‑vision operations to detect the outline of the A4 sheet and define this as the spatial reference frame for subsequent analysis. Within this automatically detected A4 region, the image is processed to segment earthworm pixels from the background and compute geometric descriptors such as total area covered by earthworms, from which effective size measures (e.g. characteristic length or footprint) can be derived. All geometric quantities are first obtained in pixel units and then transformed into physical dimensions using fixed calibration factors implied by the known dimensions of A4 paper, so that the scaling from image space to real‑world units does not depend on user tuning.

In the current implementation, these morphometric metrics are summarised as total earthworm area (and related size descriptors), providing a basis for grouping individuals into small, medium, and large classes and for estimating total earthworm mass in future versions via empirically calibrated parametric relationships. Within this framework, the user‑adjustable browser inputs control only which images are processed and any simple display options, while the Python code handles A4 detection, segmentation, feature extraction, and (once implemented) application of the size‑class grouping and mass‑calculation routines. The app returns the derived area‑based metrics together with an overlay of the detected A4 sheet and segmented earthworm regions on the original image, enabling users to visually verify that the earthworms have been correctly isolated and that the assumptions underpinning the geometric analysis are reasonable.

## Local launch & use of the app (with uv)
1. **Clone the repository:**
	```sh
	git clone https://github.com/vmyrgiotis/earthworm_mass_estimator.git
	cd earthworm_mass_estimator
	```
2. **Install [uv](https://github.com/astral-sh/uv) (if not already installed):**
	```sh
	pip install uv
	```
3. **Create and sync the environment:**
	```sh
	uv venv
	uv sync
	```
4. **Activate the virtual environment:**
	- On macOS/Linux:
	  ```sh
	  source .venv/bin/activate
	  ```
	- On Windows:
	  ```sh
	  .venv\Scripts\activate
	  ```
5. **Run the app locally:**
	```sh
	streamlit run streamlit_photo_app.py
	```

## Running the notebook

The repository also includes an example Jupyter notebook for interactive exploration and batch image processing.

### Option 1: Run Jupyter Lab inside the project environment
After creating and syncing the environment, start Jupyter Lab with:

```sh
uv run jupyter lab
```

This launches Jupyter using the project's managed environment, so the notebook can access the same dependencies as the Streamlit app. Open the notebook file from the Jupyter interface and run the cells as needed.

### Option 2: Run Jupyter Notebook instead of Lab
If you prefer the classic notebook interface, run:

```sh
uv run jupyter notebook
```

## Deployment
This app is ready for deployment on [Streamlit Cloud](https://streamlit.io/cloud).


## License
See [LICENSE](LICENSE) for details.
