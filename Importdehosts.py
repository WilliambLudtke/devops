import csv
import requests
import json

# Configurações do Zabbix
zabbix_url = 'http://192.168.3.10/zabbix/api_jsonrpc.php'  # Atualize para 'https' se necessário
username = 'Admin'  # Substitua pelo seu nome de usuário
password = 'zabbix'  # Substitua pela sua senha

def zabbix_request(method, params, auth_token=None):
    headers = {'Content-Type': 'application/json'}
    payload = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'auth': auth_token,
        'id': 1
    }
    try:
        response = requests.post(zabbix_url, headers=headers, data=json.dumps(payload), verify=False)
        response.raise_for_status()  # Levanta um erro para status HTTP não OK
        response_data = response.json()
        
        # Verificar se houve erro na resposta
        if 'error' in response_data:
            print(f"Erro na resposta da API: {response_data['error']}")
        
        return response_data
    except requests.RequestException as e:
        print(f"Erro na requisição para Zabbix: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON da resposta: {e}")
        return None

def authenticate():
    auth_params = {
        'user': username,
        'password': password
    }
    auth_response = zabbix_request('user.login', auth_params)
    if auth_response and 'result' in auth_response:
        return auth_response['result']
    else:
        print(f"Erro ao obter token de autenticação: {auth_response}")
        return None

def read_csv(file_path):
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(f"Lendo linha do CSV: {row}")  # Mensagem de depuração
                yield row
    except FileNotFoundError as e:
        print(f"Arquivo CSV não encontrado: {e}")
   
