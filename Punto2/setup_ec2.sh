#!/bin/bash

# Script de configuración para EC2
# Ejecutar como usuario ubuntu

set -e

echo "=== Actualizando sistema ==="
sudo apt update
sudo apt upgrade -y

echo "=== Instalando Python y dependencias ==="
sudo apt install -y python3-pip python3-venv

echo "=== Creando directorio de aplicación ==="
mkdir -p ~/fastapi-app
cd ~/fastapi-app

echo "=== Creando entorno virtual ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Instalando dependencias de Python ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Configurando AWS CLI ==="
sudo apt install -y awscli
echo "Configura AWS CLI con: aws configure"
echo "Necesitarás: AWS Access Key ID, Secret Access Key, región"

echo "=== Configurando systemd service ==="
sudo cp fastapi-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fastapi-app.service

echo "=== Configurando firewall ==="
sudo ufw allow 8000/tcp
sudo ufw allow ssh
echo "y" | sudo ufw enable

echo "=== Iniciando servicio ==="
sudo systemctl start fastapi-app.service
sudo systemctl status fastapi-app.service

echo ""
echo "=== Instalación completada ==="
echo "Para ver logs: sudo journalctl -u fastapi-app.service -f"
echo "Para reiniciar: sudo systemctl restart fastapi-app.service"
echo "API disponible en: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "Swagger UI: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"