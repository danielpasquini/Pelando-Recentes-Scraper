# Pelando Recentes Scraper

Este aplicativo extrai promoções da página Recentes do site Pelando e as exibe classificadas pela taxa de crescimento.

## Setup Manual

1. Clone este repositório:
git clone [https://github.com/danielpasquini/Pelando-Recentes-Scraper.git](https://github.com/danielpasquini/Pelando-Recentes-Scraper.git)

2. Crie e ative o ambiente virtual (venv):
python -m venv .venv
.venv\Scripts\activate

3. Instale os pacotes necessários:
pip install -r requirements.txt

4. Build o executável:
pyinstaller --noconfirm --windowed --onefile --strip --exclude-module test --exclude-module unittest --exclude-module tkinter --icon="<local do pelando.ico>" "<local do pelandorecentes.py>"
