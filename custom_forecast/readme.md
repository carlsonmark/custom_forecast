A Plotly Dash based custom forecast. Migraine related forecasting.

Setup
-----

Pydap is used to get the forecast data, but the pydap package on pypi is not
compatible with Python >3.8. Use the pydap submodule in this project to get
the correct version.

    cd pydap
    python setup.py install

Run
---

    python app.py

View
----

Navigate to http://localhost:8000/ in a web browser.
