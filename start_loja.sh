#!/bin/bash

cd /home/carloshenrique/Vscode/Fabrics/Loja

# Ativa o ambiente virtual
source venv/bin/activate

# Abre o navegador após 2 segundos
sleep 2 && xdg-open http://127.0.0.1:8000 &

# Inicia o Django
python manage.py runserver
