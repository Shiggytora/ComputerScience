# ✈️ Travel Matching App

An interactive web app that helps you find your perfect travel destination - based on your budget, preferences, and weather.

--------------------

## Installation:

### 1. Extract zip

### 2. Create Virtual Environment

python -m venv .venv
.venv\Scripts\activate


### 3. Install Dependencies

pip install -r requirements.txt
the api keys and secrets are also provided in the .env file


### 4. Run the App

streamlit run streamlit_app.py

The app is also available at https://computerscience91.streamlit.app/

--------------------

## Features:

### 1. Budget Filter
- Input total budget, trip duration, and number of travelers
- Automatic calculation: Flights + (Daily costs × Days × Travelers)

### 2. Travel Styles
10 predefined travel styles with weighted preferences:

### 3. Weather Integration
- Real time forecast for trips within 16 days
- Current temperature as estimate for later trips
- Weather score based on temperature preferences

### 4. Interactive Matching
- 7 rounds with 3 destinations each
- First 3 rounds: Random selection (learning preferences)
- Later rounds: Smart suggestions based on previous choices
- Preference learning through analysis of selected destinations

### 5. Similar Destinations (KNN Algorithm)
- Finds similar destinations to the top match

### 6.  Results & Visualizations
- **Hero Image** of the best destination (Unsplash)
- **Cost Breakdown**: Flights, accommodation, total, remaining budget
- **Similar Destinations**: ML-based recommendations
- **Interactive Map**: Top 5 destinations on world map
- **Charts** (Plotly):
  - Radar Chart: Preference profile
  - Bar Chart: Top 10 destinations
  - Budget Comparison: Cost comparison
  - Weather Compatibility: Weather scores

--------------------

## Credits:

- 📷 Images: [Unsplash](https://unsplash.com)
- 🌤️ Weather: [Open-Meteo](https://open-meteo.com)
- ✈️ Flight prices: [Amadeus](https://developers.amadeus.com)

--------------------

## Team:

Chiara, Jade, Jan, Morena and William as Group 9.1 in the Fundamentals and Methods of Computer Science for Business Studies course.