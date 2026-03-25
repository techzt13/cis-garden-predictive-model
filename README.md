# CISHK Garden Predictive Model

This project predicts vegetable harvest dates for the Chinese International School Hong Kong garden using Growing Degree Days (GDD). It combines historical weather data from NASA POWER with short-range forecast data from Open-Meteo, then maps that temperature history against a built-in vegetable database of crop-specific GDD targets.

The repository includes two ways to use the model:

- A Streamlit web app for interactive use in the browser
- A terminal-based CLI for quick forecasting from the command line

## Features

- Predicts harvest dates from a planting date and selected crop variety
- Uses crop-specific base temperature and target GDD requirements
- Pulls real weather data for the CISHK garden location
- Supports 500+ plant varieties in the bundled database
- Displays current progress toward harvest readiness
- Generates GDD accumulation charts in both the web app and CLI flow
- Falls back to projected harvest timing when the target is beyond the available forecast window

## Project Structure

- `app.py`: Streamlit web application
- `main.py`: terminal interactive application
- `forecast_engine.py`: forecast logic, weather data fetching, GDD calculations
- `vegetable_database.py`: plant database with base temperatures and target GDD values
- `requirements.txt`: Python dependencies

## Requirements

- Python 3.10+ recommended
- Internet access for external weather APIs

Python packages used by the app:

- `pandas`
- `numpy`
- `requests`
- `matplotlib`
- `scikit-learn`
- `streamlit`

## Installation

From the project root:

```bash
pip install -r requirements.txt
```

If your system defaults to Python 2 or you keep multiple Python versions installed, use:

```bash
python3 -m pip install -r requirements.txt
```

## Running the App

### Web App

The main interface is the Streamlit app:

```bash
streamlit run app.py
```

If `streamlit` is not available on your shell path, run:

```bash
python3 -m streamlit run app.py
```

Streamlit will start a local web server and print a URL, typically:

```text
http://localhost:8501
```

### Terminal App

To use the command-line interface instead:

```bash
python3 main.py
```

The CLI will prompt you to:

1. Search for a crop
2. Select a matching variety
3. Enter the planting date
4. Review the predicted harvest date and chart output

## How It Works

The model uses Growing Degree Days, a temperature-based measure of crop development.

The daily GDD formula used in the app is:

$$
GDD = \max\left(0, \frac{T_{max} + T_{min}}{2} - T_{base}\right)
$$

Where:

- $T_{max}$ is the daily maximum temperature
- $T_{min}$ is the daily minimum temperature
- $T_{base}$ is the crop-specific base temperature

Forecast flow:

1. Load the crop's base temperature and target GDD from the plant database.
2. Fetch historical daily temperature data from NASA POWER.
3. Fetch a 7-day forecast from Open-Meteo.
4. Calculate daily GDD values from the planting date onward.
5. Accumulate GDD until the crop's target is reached.
6. If the target is not reached within available data, estimate remaining time using the average historical daily GDD rate.

## Data Sources

The app currently uses weather data for the CISHK garden coordinates:

- Latitude: `22.2855`
- Longitude: `114.1989`

External data providers:

- NASA POWER: historical daily max/min temperature data
- Open-Meteo: short-range daily forecast data

## Using the Web App

The Streamlit app provides:

- Plant search field
- Variety dropdown with GDD and base temperature details
- Planting date picker
- Harvest prediction summary
- Progress metrics
- GDD accumulation chart
- A detailed timeline table showing recent GDD values

## Using the CLI

The terminal app provides:

- Text-based crop search
- Numbered crop selection
- Planting date input in `YYYY-MM-DD` format
- Printed harvest forecast summary
- Saved chart image as `harvest_forecast.png`

## Output Details

Prediction results may include:

- Selected plant name
- Base temperature
- Target GDD
- Planting date
- Current accumulated GDD
- Harvest date estimate
- Days from planting to harvest
- Confidence level
- Uncertainty estimate for projected forecasts
- A note explaining when projected data was used

Confidence values currently behave as follows:

- `HIGH`: target GDD reached within the combined historical plus short-range forecast data
- `MEDIUM`: harvest date projected using an average historical daily GDD rate

## Example Commands

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the web app:

```bash
python3 -m streamlit run app.py
```

Run the terminal app:

```bash
python3 main.py
```

## Known Limitations

- The app depends on live external APIs, so it will not work correctly without internet access.
- The forecast location is fixed to the CISHK garden coordinates unless code changes are made.
- Projected harvest dates beyond the available forecast range use an average historical GDD rate, so they are estimates rather than full weather-driven forecasts.
- The plant database is static and embedded directly in source code.
- The chart and timeline reflect the data made available by the fetched history and forecast window.

## Troubleshooting

### `streamlit: command not found`

Use:

```bash
python3 -m streamlit run app.py
```

### Dependency install issues

Make sure you are using the same Python interpreter for both install and run commands.

Example:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

### No prediction returned

Possible causes:

- Plant name is not in the database
- Planting date is outside the usable data window
- Weather API request failed
- Forecast projection could not compute an average GDD rate

## Development Notes

Core implementation details:

- Weather retrieval and GDD logic live in `forecast_engine.py`
- The plant database is stored as a Python dictionary in `vegetable_database.py`
- The Streamlit app is the best entry point for most users
- The CLI remains useful for quick testing and non-browser environments

## License / Attribution

This repository currently does not define a software license file. If you plan to distribute or reuse it outside private/internal use, add an explicit license.