# Run this app with `python app.py` and
# visit http://127.0.0.1:8000/ in your web browser.

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from dash_bootstrap_templates import ThemeSwitchAIO

from custom_forecast.forecast import latest_data_frames
from custom_forecast.forecast_thread import ForecastThread

DEFAULT_PLOT_TEMPLATE = 'cyborg'


def figures(template):
    data_frames = latest_data_frames()
    margin = dict(l=40, r=40, t=30, b=1)
    height = 250
    # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html
    # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html
    figure = go.Figure(
        [go.Scatter(x=df['time'], y=df['pressure']) for df in data_frames],
        layout_yaxis_range=[97, 105])
    figure.update_layout(showlegend=False,
                         template=template,
                         margin=margin,
                         height=height,
                         title='Sea Level Pressure (kPa)')
    figure.update_yaxes(tickmode='linear', tick0=0, dtick=1)
    figure.update_xaxes(tickmode='linear',
                        tick0=pd.Timestamp.now().date(),
                        dtick=pd.Timedelta(days=1))
    # Add a line that indicates the current time
    figure.add_vline(x=pd.Timestamp.now())

    derivative_figure = go.Figure(
        [go.Scatter(x=df['time'], y=df['derivative']) for df in data_frames],
        layout_yaxis_range=[-3, 3])
    derivative_figure.update_layout(showlegend=False,
                                    template=template,
                                    margin=margin,
                                    height=height,
                                    title='Pressure change, (kPa per day)')
    derivative_figure.update_yaxes(tickmode='linear', tick0=0, dtick=0.5)
    derivative_figure.update_xaxes(tickmode='linear',
                                   tick0=pd.Timestamp.now().date(),
                                   dtick=pd.Timedelta(days=1))
    # Add a line that indicates the current time
    derivative_figure.add_vline(x=pd.Timestamp.now())
    derivative_figure.add_hline(y=0, line_dash='dash', line_color='green')
    derivative_figure.add_hline(y=-2, line_dash='dash', line_color='red')
    derivative_figure.add_hline(y=2, line_dash='dash', line_color='red')
    derivative_figure.add_hline(y=-1, line_dash='dash', line_color='yellow')
    derivative_figure.add_hline(y=1, line_dash='dash', line_color='yellow')

    return [figure, derivative_figure]


def forecast_links():
    links = [
        dbc.Button('Env. Can.', className='me-2', href='https://weather.gc.ca/city/pages/ab-52_metric_e.html'),
        dbc.Button('GDPS 3.5d', className='me-2', href='https://spotwx.com/products/grib_index.php?model=gem_reg_10km&lat=51.11753&lon=-113.93191&tz=America/Edmonton'),
        dbc.Button('GDPS 10d', className='me-2', href='https://spotwx.com/products/grib_index.php?model=gem_glb_15km&lat=51.11753&lon=-113.93191&tz=America/Edmonton'),
        dbc.Button('Windy', className='me-2', href='https://www.windy.com/51.115/-113.937?51.090,-113.937,12,m:e4macZh'),
    ]  # yapf: disable
    return html.Div(links)


def app_layout():
    theme_switch = ThemeSwitchAIO(aio_id='theme',
                                  switch_props=dict(value=False),
                                  themes=[dbc.themes.COSMO, dbc.themes.QUARTZ])
    layout = dbc.Container(
        [
            theme_switch,
            html.P('Forecast for Calgary'),
            dcc.Graph(id='pressure-forecast', figure=go.Figure(layout=dict(template=DEFAULT_PLOT_TEMPLATE))),
            dcc.Graph(id='pressure-forecast-derivative', figure=go.Figure(layout=dict(template=DEFAULT_PLOT_TEMPLATE))),
            html.P('Other forecasts'),
            forecast_links(),
        ],
        fluid=True,
    )  # yapf: disable
    return layout


external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = app_layout()


# It seems like this callback should be able to update just the figure's themes...
# But the demo updates the whole figure...
@app.callback(
    [
        Output('pressure-forecast', 'figure'),
        Output('pressure-forecast-derivative', 'figure'),
    ],
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def update_graph_theme(toggle):
    template = 'cosmo' if toggle else DEFAULT_PLOT_TEMPLATE
    return figures(template=template)


if __name__ == '__main__':
    forecast_thread = ForecastThread.instance()
    forecast_thread.start()
    app.run_server(host='192.168.1.6', port=8000, debug=True)
