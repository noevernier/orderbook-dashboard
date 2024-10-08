import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import datetime

class OrderbookHeatmap:
    def __init__(self, csv_file):
        self.app = dash.Dash(__name__)
        self.zmin = 0
        self.zmax = 300
        self.csv_file = csv_file
        self.setup_layout()
        self.setup_callbacks()
        self.df = pd.DataFrame(columns=["timestamp", "price", "amount", "side"])

    def setup_layout(self):
        self.app.index_string = open("dashboard/assets/index.html", "r").read()

        self.app.layout = html.Div(
            [
                dcc.Graph(id="heatmap", style={"height": "90vh", "width": "100vw"}),
                html.Div(
                    [
                        dcc.RangeSlider(
                            id="z-slider",
                            min=0,
                            max=1000,
                            step=1,
                            marks={i: str(i) for i in range(0, 1001, 100)},
                            value=[self.zmin, self.zmax],
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                        html.Div(
                            id="slider-output",
                            style={"color": "#636D7D", "fontFamily": "Roboto"},
                        ),
                    ],
                    style={"width": "50%", "padding": "1px", "margin": "0 auto"},
                ),
                dcc.Interval(
                    id="interval-component",
                    interval=60*1000,  # Update every 60 seconds
                    n_intervals=0,
                ),
            ],
            style={
                "height": "100%",
                "width": "100%",
                "display": "flex",
                "flexDirection": "column",
                "backgroundColor": "#121212",
                "margin": "0",
                "padding": "0",
            },
        )

    def setup_callbacks(self):
        @self.app.callback(
            Output("heatmap", "figure"),
            [Input("interval-component", "n_intervals"), Input("z-slider", "value")],
        )
        def update_heatmap(n, z_range):
            self.zmin, self.zmax = z_range

            self.df = pd.read_csv(self.csv_file)
            self.df.columns = ["timestamp", "price", "amount", "side"]
            
            self.df["timestamp"] = pd.to_datetime(self.df["timestamp"], format="%Y-%m-%d %H:%M")
            
            recent_time_limit = datetime.datetime.now() - datetime.timedelta(minutes=100)
            self.df = self.df[self.df["timestamp"] > recent_time_limit]
                        
            return self.create_heatmap()

    def create_heatmap(self):
        if self.df.empty:
            return go.Figure()
        

        df = (
            self.df.groupby(["timestamp", "price", "side"])
            .agg({"amount": "sum"})
            .reset_index()
        )

        mid_price = (
            df[df.side == "ask"].groupby("timestamp").price.min()
            + df[df.side == "bid"].groupby("timestamp").price.max()
        ) / 2

        all_prices = np.arange(
            np.ceil(mid_price.min() * 0.98 / 20) * 20,
            np.floor(mid_price.max() * 1.02 / 20) * 20 + 20,
            20,
        )
        timestamps = df.timestamp.unique()
        heatmap_data = np.zeros((len(all_prices), len(timestamps)))

        price_to_index = {price: idx for idx, price in enumerate(all_prices)}
        timestamps_to_index = {ts: idx for idx, ts in enumerate(timestamps)}

        grouped = df.groupby(["timestamp", "price"]).amount.sum().reset_index()

        for row in grouped.itertuples(index=False):
            if row.price in price_to_index:
                heatmap_data[
                    price_to_index[row.price], timestamps_to_index[row.timestamp]
                ] = row.amount

        fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_data,
                x=timestamps,
                y=all_prices,
                colorscale="Viridis",
                zmin=self.zmin,
                zmax=self.zmax,
                showscale=False,
            )
        )
        fig.update_traces(name="Amount", hovertemplate="<b> %{z:.2f}<br>")

        # Midprice line
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=mid_price,
                mode="lines",
                line=dict(color="red", width=2),
                showlegend=False,
            )
        )

        fig.update_traces(hoverinfo="skip", selector=dict(type="scatter", mode="lines"))

        fig.update_layout(
            title={
                "text": "BTCUSDT OrderBook Heatmap",
                "font": {
                    "size": 24,
                    "family": "Roboto",
                    "weight": "bold",
                    "color": "#E0E0E0",
                },
            },
            yaxis=dict(
                title={
                    "text": "Price",
                    "font": {
                        "size": 10,
                        "family": "Roboto",
                        "weight": "bold",
                        "color": "#636D7D",
                    },
                },
                tickfont=dict(color="#636D7D"),
                tickformat=",.0f",
                side="right",
            ),
            xaxis=dict(
                title={
                    "text": "Timestamp",
                    "font": {
                        "size": 10,
                        "family": "Roboto",
                        "weight": "bold",
                        "color": "#636D7D",
                    },
                },
                tickfont=dict(color="#636D7D"),
            ),
            uirevision=True,
            template="plotly_dark",
            dragmode="zoom",
            hovermode="y unified",
            modebar=dict(
                orientation="v",
                bgcolor="#333333",
                color="#E0E0E0",
            ),
        )

        fig.update_yaxes(fixedrange=False)
        fig.update_xaxes(fixedrange=False)

        return fig

    def run(self):
        PORT = 8060
        HOST = '0.0.0.0'
        self.app.run_server(debug=False, port=PORT, host=HOST)


# Utilisation de la classe
csv_file = "data_snapshot.csv"
heatmap = OrderbookHeatmap(csv_file)
heatmap.run()
