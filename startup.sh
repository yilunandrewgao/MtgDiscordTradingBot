#!/bin/bash
sudo apt update
sudo apt install python3
sudo apt install python3-pip
sudo apt install python3.11-venv
sudo apt-get install git-all
git clone https://github.com/yilunandrewgao/MtgDiscordTradingBot.git
cd discordTradingBot
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt 
export PYTHONPATH=/home/yilungao/git/MtgDiscordTradingBot/src

python3 -m src.main
