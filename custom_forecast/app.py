# Run this app with `python app.py` and
# visit http://127.0.0.1:8000/ in your web browser.

import time

import dash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from forecast import get_pressure, get_urls
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.signal import savgol_filter


def pressure_derivative(pressure: pd.array,
                        derivative_scale: float = 20) -> pd.array:
    x = np.arange(len(pressure))
    filtered_pressure = savgol_filter(pressure, len(pressure) // 8, 3)
    f = InterpolatedUnivariateSpline(x, filtered_pressure, k=1)
    derivative = f.derivative()(x) * derivative_scale
    return derivative


urls = get_urls(-5, None)
data_frames = []

# Load data from files for testing, since the server has low limits on how
# many times you can use it before it blocks you.
load_data = True
if load_data:
    file_counter = 0
    file_found = True
    while file_found:
        try:
            df = pd.read_pickle(f'data-{file_counter}.pkl')
            df['derivative'] = pressure_derivative(df['pressure'])
            data_frames.append(df)
            file_counter += 1
        except FileNotFoundError as e:
            file_found = False
else:
    for i, url in enumerate(urls):
        pressure, time_, lat, lon = get_pressure(51.05, 114.0677, url)
        time_offset = (-time.timezone) / (24.0 * 3600.0)
        time_with_offset = time_ + time_offset
        ordinal_date = time_.astype(int)
        fractional_date = time_ - ordinal_date
        seconds = (fractional_date * (24 * 60 * 60)).astype(int)
        timestamp = pd.array(
            [pd.Timestamp.fromordinal(d) for d in ordinal_date])
        timedelta = pd.array([pd.Timedelta(seconds=s) for s in seconds])
        df = pd.DataFrame(
            dict(time=timestamp + timedelta,
                 pressure=pressure,
                 derivative=pressure_derivative(pressure)))
        df.to_pickle(f'data-{i}.pkl')
        data_frames.append(df)

# https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html
# https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html
figure = go.Figure([
    go.Scatter(x=df['time'], y=df['pressure'])
    for df in data_frames
],
                   layout_yaxis_range=[97, 105])
figure.update_layout(showlegend=False)
figure.update_yaxes(tickmode='linear', tick0=0, dtick=1)
figure.update_xaxes(tickmode='linear',
                    tick0=pd.Timestamp.now().date(),
                    dtick=pd.Timedelta(days=1))
# Add a line that indicates the current time
figure.add_vline(x=pd.Timestamp.now())

derivative_figure = go.Figure([
    go.Scatter(x=df['time'], y=df['derivative'])
    for df in data_frames
],
                              layout_yaxis_range=[-3, 3])
derivative_figure.update_layout(showlegend=False)
derivative_figure.update_yaxes(tickmode='linear', tick0=0, dtick=0.5)
derivative_figure.update_xaxes(tickmode='linear',
                               tick0=pd.Timestamp.now().date(),
                               dtick=pd.Timedelta(days=1))
# Add a line that indicates the current time
derivative_figure.add_vline(x=pd.Timestamp.now())

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.P('Forecast for Calgary'),
        dcc.Graph(id='pressure-forecast', figure=figure),
        dcc.Graph(id='pressure-forecast-derivative', figure=derivative_figure),
    ]
)  # yapf: disable


if __name__ == '__main__':
    app.run_server(host='192.168.1.6', port=8000, debug=True)
