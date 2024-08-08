import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import datetime
import numpy as np

class Strategy:
    def __init__(self, initial_balance=10000, fee_rate=0.0004):
        self.app = dash.Dash(__name__)
        self.initial_balance = initial_balance
        self.fee_rate = fee_rate
        self.current_balance = initial_balance
        self.current_btc = 0
        self.portfolio_df = pd.DataFrame(columns=['timestamp', 'portfolio_value', 'buy_and_hold_value'])
        self.volume_imbalance_df = pd.DataFrame(columns=['timestamp', 'volume_imbalance'])
        self.btc_price = 0
        self.last_trade_time = None
        self.trade_action = None
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        self.app.layout = html.Div([
            dcc.Graph(id='portfolio-chart', style={'height': '90vh', 'width': '100vw'}),
            dcc.Interval(
                id='interval-component',
                interval=1000,  # Update every second
                n_intervals=0
            )
        ], style={'height': '100%', 'width': '100%', 'display': 'flex', 'flexDirection': 'column', 'backgroundColor': '#121212', 'margin': '0', 'padding': '0'})

    def setup_callbacks(self):
        @self.app.callback(
            Output('portfolio-chart', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_portfolio_chart(n):
            # Récupération des valeurs de volume imbalance et du prix du BTC
            amount_ask = requests.get('http://127.0.0.1:5000/volume_ask').json()
            amount_bid = requests.get('http://127.0.0.1:5000/volume_bid').json()
            
            total_volume = amount_ask + amount_bid
            volume_imbalance = (amount_bid - amount_ask ) / total_volume if total_volume != 0 else 0
            snapshot = requests.get('http://127.0.0.1:5000/snapshot').json()
            snapshot = pd.DataFrame(snapshot)
            self.btc_price = snapshot[snapshot['side'] == 'bid']['price'].max()
            timestamp = datetime.datetime.now().timestamp() * 1e6  # microsecondes

            # Ajout des nouvelles données de volume imbalance
            new_data = pd.DataFrame({
                'timestamp': [timestamp],
                'volume_imbalance': [volume_imbalance]
            })
            self.volume_imbalance_df = pd.concat([self.volume_imbalance_df, new_data], ignore_index=True)

            # Calcul des seuils de 80% et 20% sur une fenêtre de 10 minutes
            window_size = 10* 60 * 1000  # 10 minutes en millisecondes
            now = datetime.datetime.now().timestamp() * 1e6
            recent_data = self.volume_imbalance_df[self.volume_imbalance_df['timestamp'] >= (now - window_size)]
            
            if len(recent_data) > 0:
                rolling_quantile_80 = recent_data['volume_imbalance'].rolling(window=len(recent_data), min_periods=1).quantile(0.80).iloc[-1]
                rolling_quantile_20 = recent_data['volume_imbalance'].rolling(window=len(recent_data), min_periods=1).quantile(0.20).iloc[-1]
            else:
                rolling_quantile_80 = rolling_quantile_20 = 0  # Par défaut

            # Exécution de la stratégie
            if self.last_trade_time:
                trade_elapsed_time = datetime.datetime.now() - self.last_trade_time
                if trade_elapsed_time.total_seconds() < 60:
                    return self.create_portfolio_chart()  # Pas assez de temps écoulé pour le prochain trade

            if volume_imbalance > rolling_quantile_80 and self.current_btc == 0:
                # Achat de BTC
                amount_to_buy = self.current_balance / self.btc_price
                self.current_btc = amount_to_buy
                self.current_balance = 0
                self.last_trade_time = datetime.datetime.now()
                self.trade_action = 'buy'

            elif volume_imbalance < rolling_quantile_20 and self.current_btc > 0:
                # Vente de BTC
                self.current_balance = self.current_btc * self.btc_price * (1 - self.fee_rate)
                self.current_btc = 0
                self.last_trade_time = datetime.datetime.now()
                self.trade_action = 'sell'

            # Mise à jour de la valeur du portefeuille
            portfolio_value = self.current_balance + (self.current_btc * self.btc_price)
            buy_and_hold_value = self.initial_balance / self.btc_price * self.btc_price

            # Ajouter les données au DataFrame
            new_data = pd.DataFrame({
                'timestamp': [timestamp],
                'portfolio_value': [portfolio_value],
                'buy_and_hold_value': [buy_and_hold_value]
            })
            self.portfolio_df = pd.concat([self.portfolio_df, new_data], ignore_index=True)

            return self.create_portfolio_chart()

    def create_portfolio_chart(self):
        # Convertir les timestamps en format datetime pour les axes du graphique
        self.portfolio_df['datetime'] = pd.to_datetime(self.portfolio_df['timestamp'], unit='us')

        # Création des sous-graphiques
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=("Portfolio Value vs Buy and Hold Value")
        )

        # Trace pour la valeur du portefeuille
        fig.add_trace(go.Scatter(
            x=self.portfolio_df['datetime'],
            y=self.portfolio_df['portfolio_value'],
            mode='lines',
            line=dict(color='blue', width=2),
            name='Strategy Portfolio Value'
        ))

        # Trace pour la valeur buy and hold
        fig.add_trace(go.Scatter(
            x=self.portfolio_df['datetime'],
            y=self.portfolio_df['buy_and_hold_value'],
            mode='lines',
            line=dict(color='green', width=2),
            name='Buy and Hold Value'
        ))

        # Mise à jour de la disposition
        fig.update_layout(
            height=800,  # Hauteur du graphique
            title={'text': 'Portfolio Value vs Buy and Hold', 'font': {'size': 24, 'family': 'Roboto', 'weight': 'bold', 'color': '#E0E0E0'}},
            template='plotly_dark',
            hovermode='x unified',
            showlegend=True,
            xaxis=dict(
                tickfont=dict(color='#636D7D'),
            ),
            yaxis=dict(
                tickfont=dict(color='#636D7D'),
            )
        )

        return fig

    def run(self):
        self.app.run_server(debug=False)

# Pour exécuter le tableau de bord:
if __name__ == "__main__":
    strategy = Strategy()
    strategy.run()
