# Run this app with `python app.py` and
# visit http://127.0.0.1:8080/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go
import matplotlib.dates as dates

from forecast import getPressure, getUrls
from utils import ordinalUtc2localtime


def convertDataFrameTimestamp(
        dataFrame: pd.DataFrame, key: str, timeZone: str = 'America/Edmonton'):
    """
    Convert timestamps in a DataFrame from epoch time to a datetime that
    works well for plotting.
    :param dataFrame: The DataFrame to convert data in
    :param key: The key for the data
    :param timeZone: The timezone to convert the timestamp to
    """
    ordinal = dataFrame[key]
    localtimes = ordinalUtc2localtime(ordinal - 1)
    datetimes = dates.num2date(localtimes)
    dataFrame[key] = pd.to_datetime(datetimes)
    # .dt.tz_localize('utc').dt.tz_convert(timeZone)
    return


urls = getUrls(-5, None)
dataFrames = []

# Load data from files for testing, since the server has low limits on how
# many times you can use it before it blocks you.
loadData = False
if loadData:
    fileCounter = 0
    fileFound = True
    while fileFound:
        try:
            df = pd.read_pickle(f'data-before-{fileCounter}.pkl')
            convertDataFrameTimestamp(df, 'time')
            dataFrames.append(df)
            fileCounter += 1
        except FileNotFoundError as e:
            fileFound = False
else:
    fileCounter = 0
    for url in urls:
        pressure, time, lat, lon = getPressure(51.05, 114.0677, url)
        df = pd.DataFrame(dict(time=time,
                    pressure=pressure))
        df.to_pickle(f'data-before-{fileCounter}.pkl')
        convertDataFrameTimestamp(dataFrame=df, key='time')
        dataFrames.append(
            df
        )
        df.to_pickle(f'data-{fileCounter}.pkl')
        fileCounter += 1

# https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html
# https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html
figure = go.Figure([
        go.Scatter(x=df['time'], y=df['pressure'])
    for df in dataFrames])
figure.update_layout(yaxis_range=[97, 105])
figure.update_yaxes(tick0=0, dtick=1.0)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.P('Forecast for Calgary'),
        dcc.Graph(id='pressure-forecast', figure=figure),
    ]
)  # yapf: disable


if __name__ == '__main__':
    # app.run_server(host='192.168.1.70', port=8080, debug=True)
    app.run_server(port=8080, debug=True)
