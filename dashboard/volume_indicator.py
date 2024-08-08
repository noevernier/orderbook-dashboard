import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import datetime

class VolumeIndicator:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.df = pd.DataFrame(columns=['timestamp', 'amount_ask', 'amount_bid', 'total_volume', 'volume_imbalance'])
        self.setup_layout()
        self.setup_callbacks()

        self.pnl = 1

    def setup_layout(self):
        self.app.index_string = open('dashboard/assets/index.html', 'r').read()

        self.app.layout = html.Div([
            dcc.Graph(id='volume-chart', style={'height': '90vh', 'width': '100vw'}),
            dcc.Interval(
                id='interval-component',
                interval=1000,  # Update every second
                n_intervals=0
            )
        ], style={'height': '100%', 'width': '100%', 'display': 'flex', 'flexDirection': 'column', 'backgroundColor': '#121212', 'margin': '0', 'padding': '0'})

    def setup_callbacks(self):
        @self.app.callback(
            Output('volume-chart', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_volume_chart(n):
            amount_ask = requests.get('http://13.60.169.158:5000/volume_ask').json()
            amount_bid = requests.get('http://13.60.169.158:5000/volume_bid').json()
            
            total_volume = amount_ask + amount_bid
            volume_imbalance = (amount_bid - amount_ask ) / total_volume if total_volume != 0 else 0
            
            timestamp = datetime.datetime.now().timestamp() * 1e6  # microsecondes

            new_data = pd.DataFrame({
                'timestamp': [timestamp],
                'amount_ask': [amount_ask],
                'amount_bid': [amount_bid],
                'total_volume': [total_volume],
                'volume_imbalance': [volume_imbalance]
            })
            self.df = pd.concat([self.df, new_data], ignore_index=True)

            # Filtrage pour les 5 dernières minutes
            now = datetime.datetime.now()
            five_minutes_ago = now - datetime.timedelta(minutes=5)
            five_minutes_ago_timestamp = five_minutes_ago.timestamp() * 1e6  # microsecondes
            self.df = self.df[self.df['timestamp'] >= five_minutes_ago_timestamp]

            return self.create_volume_chart()

    def create_volume_chart(self):
        self.df['datetime'] = pd.to_datetime(self.df['timestamp'], unit='us')

        fig = make_subplots(
            rows=2, cols=2,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Volume Ask", "Total Volume","Volume Bid" , "Volume Imbalance")
        )

        fig.add_trace(go.Scatter(
            x=self.df['datetime'],
            y=self.df['amount_ask'],
            mode='lines',
            line=dict(color='orange', width=2),
            name='Volume Ask',
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=self.df['datetime'],
            y=self.df['amount_bid'],
            mode='lines',
            line=dict(color='green', width=2),
            name='Volume Bid',
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=self.df['datetime'],
            y=self.df['total_volume'],
            mode='lines',
            line=dict(color='blue', width=2),
            name='Total Volume',
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=self.df['datetime'],
            y=self.df['volume_imbalance'],
            mode='lines',
            line=dict(color='red', width=2),
            name='Volume Imbalance',
        ), row=2, col=2)

        # add rolling quantile q=0.75
        q = 0.80
        fig.add_trace(go.Scatter(
            x=self.df['datetime'],
            y=self.df['volume_imbalance'].rolling(window=5*60).quantile(q),
            mode='lines',
            line=dict(color='orange', width=1, dash='dash'),
            name='Volume Imbalance 75%',
        ), row=2, col=2)

        fig.add_trace(go.Scatter(
            x=self.df['datetime'],
            y=self.df['volume_imbalance'].rolling(window=5*60).quantile(1-q),
            mode='lines',
            line=dict(color='green', width=1, dash='dash'),
            name='Volume Imbalance 25%',
        ), row=2, col=2)

        fig.update_layout(
            title={'text': 'Volume Indicator', 'font': {'size': 24, 'family': 'Roboto', 'weight': 'bold', 'color': '#E0E0E0'}},
            template='plotly_dark',
            hovermode='x unified',
            showlegend=False,
            xaxis=dict(
                tickfont=dict(color='#636D7D'),
            ),
            yaxis=dict(
                tickfont=dict(color='#636D7D'),
            )
        )

        fig.update_yaxes(title_text="Volume Ask", row=1, col=1, tickfont=dict(color='#636D7D'))
        fig.update_yaxes(title_text="Volume Bid", row=2, col=1, tickfont=dict(color='#636D7D'))
        fig.update_yaxes(title_text="Total Volume", row=1, col=2, tickfont=dict(color='#636D7D'))
        fig.update_yaxes(title_text="Volume Imbalance", row=2, col=2, tickfont=dict(color='#636D7D'))
        fig.update_xaxes(title_text="Timestamp", tickfont=dict(color='#636D7D'))

        return fig

    def run(self):
        self.app.run_server(debug=False)

if __name__ == "__main__":
    indicator = VolumeIndicator()
    indicator.run()
