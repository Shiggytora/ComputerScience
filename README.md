How to install:

# clone the repository
git clone https://github.com/Shiggytora/ComputerScience.git

# navigate to the repository
cd ComputerScience

# create a virtuell environment
python -m venv .venv

# install dependencies/libraries
pip install -r requirements.txt

# run streamlit/start the app
streamlit run streamlit_app.py# ✈️ Travel Matching Recommender

A machine learning-powered travel destination recommender built with Streamlit. 

# Problem Statement

Choosing a travel destination can be overwhelming with hundreds of options available. This application solves this problem by:
1. Learning user preferences through an interactive matching process
2. Using machine learning to calculate compatibility scores
3. Incorporating real-time weather data for better recommendations

# Features

- **Interactive Matching**: 7-round process to learn your preferences
- **7 Travel Styles**: Beach, City, Budget, Hidden Gem, Luxury, Adventure, Balanced
- **Weather Integration**: Real-time weather data from Open-Meteo API
- **ML-Powered Scoring**: Weighted similarity algorithm learns your preferences
- **Detailed Insights**: Understand why destinations match your preferences
- **Export Results**: Download your results as JSON