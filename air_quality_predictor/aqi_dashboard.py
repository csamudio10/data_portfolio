import streamlit as st
import pandas as pd
import numpy as np

st.title('Air Quality in Usaquen')

data_url = 'https://github.com/csamudio10/portfolio/blob/main/air_quality_predictor/aqi_usaquen.csv'
date_column = 'time'

def load_data(nrows):
    data = pd.read_csv(data_url, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[date_column] = pd.to_datetime(data[DATE_COLUMN])
    return data

data_load_state = st.text('Loading data...')
data = load_data(100)
data_load_state.text("Done! (using st.cache_data)")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

