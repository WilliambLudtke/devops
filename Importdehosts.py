import csv
import requests
import json

# Configurações do Zabbix
zabbix_url = 'http://192.168.3.10/zabbix/api_jsonrpc.php'
username = 'Admin'
password = 'zabbix'

def zabbix_request(method, params, auth_token=None):
    headers = {'Content-Type': 'application/json'}
    payload = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'auth': auth_token,
        'id': 1
    }
    response = requests.post(zabbix_url, headers=headers, data=json.dumps(payload))
    return response.json()

def read_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield row

try:
    # Solicitar o ID do hostgroup do usuário
    hostgroup_id = input("Digite o ID do hostgroup do Zabbix: ")

    # Solicitar o ID do template do usuário
    template_id = input("Digite o ID do template do Zabbix: ")

    # Autenticar e obter o token de autenticação
    auth_response = zabbix_request('user.login', {'user': username, 'password': password})
    if 'result' in auth_response:
        auth_token = auth_response['result']
    else:
        raise Exception(f"Erro ao autenticar: {auth_response}")

    contador = 0

    # Loop para criar hosts
    for i, data in enumerate(read_csv('ficha.csv'), 1):
        contador += 1

        host_name = data['Host name']
        ip_address = data['IP']
        description = data['Descrição']
        so_or_network = data['SO ou Ativo de Rede']

        try:
            if so_or_network.lower() == 'so':
                # Criar host para SO
                host_create_response = zabbix_request('host.create', {
                    'host': host_name,
                    'status': 1,
                    'interfaces': [{
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": ip_address,
                        "dns": "",
                        "port": "10050"
                    }],
                    'groups': [{"groupid": hostgroup_id}],
                    'templates': [{"templateid": template_id}],
                    'description': description
                }, auth_token)

            elif so_or_network.lower() == 'ativo de rede':
                # Criar host para Ativo de Rede com os detalhes adicionais
                host_create_response = zabbix_request('host.create', {
                    'host': host_name,
                    'status': 1,
                    'interfaces': [{
                        "type": 2,
                        "main": 1,
                        "useip": 1,
                        "ip": ip_address,
                        "dns": "",
                        "port": "161",
                        "details": {
                            "version": 2,
                            "bulk": 0,
                            "community": "public"
                        }
                    }],
                    'groups': [{"groupid": hostgroup_id}],
                    'templates': [{"templateid": template_id}],
                    'description': description
                }, auth_token)

            if 'result' in host_create_response:
                print(f"""
                Host criado: {host_name},
                IP Atribuído: {ip_address},
                Descrição: {description},
                SO ou Ativo de Rede: {so_or_network}""")
            else:
                print(f"Erro ao criar host {host_name}: {host_create_response}")

        except Exception as e:
            print(f"Erro ao criar host {host_name}: {e}")
            contador -= 1

    print(f"Número de novos Hosts criados: {contador}")

except Exception as e:
    print(f"Erro geral: {e}")

finally:
    # Logout após criar os hosts
    logout_response = zabbix_request('user.logout', {}, auth_token)
    if 'result' in logout_response:
        print("Logout realizado com sucesso.")
    else:
        print(f"Erro ao fazer logout: {logout_response}")
