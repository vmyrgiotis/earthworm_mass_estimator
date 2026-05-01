# Earthworm Mass Estimator

A Streamlit app to estimate earthworm area (and, soon, mass) from photos. Deployable on Streamlit Cloud. Available [here](https://vmyrgiotis-earthworm-mass-estimator-streamlit-photo-app-gmcyje.streamlit.app)

## Features
- Upload a photo and estimate earthworm mass
- Simple, interactive Streamlit interface

## Methodology 

The algorithm is implemented in Python and provided as an application with a browser-based interface built on Streamlit Community Cloud. It currently performs a semi‑automated, image‑based estimate of earthworm body area (and, in future versions, will provide fresh mass estimation), using a photo of worms placed on a printed A4 reference sheet.

Methodologically, the tool applies a sequence of basic computer‑vision operations to detect the outline of the A4 sheet and define this as the spatial reference frame for subsequent analysis. Within this frame, the app segments the earthworm(s) from the background based on color and morphological operations.

In the current implementation, these morphometric metrics are summarised as total earthworm area (and related size descriptors), providing a basis for grouping individuals into small, medium, and large categories.

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

