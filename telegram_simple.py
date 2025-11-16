#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import requests
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = '7824400107:AAGZqPdS0E0N3HsYpD8TW9m8c-bapFd-RHk'
CHANNEL_ID = '@TrueLiveBet'
current_time = datetime.now().strftime('%H:%M')

# Читаем актуальный анализ из файла
try:
    with open('current_live_analysis_mcp.txt', 'r', encoding='utf-8') as f:
        message = f.read()
except FileNotFoundError:
    message = f'''🧠 ИИ-АНАЛИЗ LIVE • {current_time} МСК • Честно и просто

⚠️ Ошибка: файл анализа не найден
Проверьте актуальные матчи на BetBoom

🤝 @TrueLiveBet - честный ИИ-анализ для всех'''

url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
data = {'chat_id': CHANNEL_ID, 'text': message} # Removed parse_mode='Markdown'

try:
    response = requests.post(url, data=data, verify=False)
    result = response.json()
    
    if result.get('ok'):
        print('MCP ANALIZ OTPRAVLEN V @TrueLiveBet!')
        print(f'Message ID: {result["result"]["message_id"]}')
    else:
        print(f'Error: {result}')
        
except Exception as e:
    print(f'Ошибка: {e}')
