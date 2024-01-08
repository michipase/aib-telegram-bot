sudo apt update
sudo apt install python3 wkhtmltopdf libxml2-dev libxslt1-dev -y
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
echo "DONE!"
