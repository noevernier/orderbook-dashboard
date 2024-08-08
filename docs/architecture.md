# Architecture du Projet

## Vue d'ensemble

Le projet se compose de deux parties principales : un **serveur Flask** qui collecte et agrège les données d'order book, et un **dashboard Dash** qui visualise ces données sous forme de heatmap.

### Serveur Flask

- **Objectif**: Collecter les données en temps réel via une WebSocket, les organiser dans un order book, et exposer une API pour obtenir les instantanés.
- **Fichiers principaux**:
  - `app.py`: Lance le serveur Flask.
  - `orderbook.py`: Gère la logique de l'order book.
  - `utils.py`: Contient des fonctions utilitaires.

### Dashboard Dash

- **Objectif**: Visualiser les données de l'order book en utilisant un graphique de heatmap.
- **Fichiers principaux**:
  - `app.py`: Lance l'application Dash.
  - `heatmap.py`: Contient la logique de création de la heatmap.
  - `assets/`: Contient les fichiers CSS et JS personnalisés.

### Tests

- **Objectif**: S'assurer que chaque composant du système fonctionne correctement.
- **Structure**:
  - `test_server.py`: Tests pour le serveur Flask.
  - `test_dashboard.py`: Tests pour le dashboard Dash.

## Flux de Données

1. **Collecte des Données**: Les données sont collectées via une WebSocket en temps réel.
2. **Agrégation**: Les données sont agrégées dans l'order book et nettoyées régulièrement.
3. **API**: Le serveur Flask expose un endpoint `/snapshot` pour obtenir un instantané de l'order book.
4. **Visualisation**: Le dashboard Dash récupère ces instantanés et les affiche sous forme de heatmap.