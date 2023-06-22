#!bin/bash

sudo apt update && apt upgrade -y
sudo apt-get install wkhtmltopdf
pip install requirements.txt