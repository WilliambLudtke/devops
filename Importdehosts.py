import csv
import requests
import json

# Configurações do Zabbix
zabbix_url = 'http://192.168.3.10/zabbix/api_jsonrpc.php'  # Substitua pelo URL do seu servidor Zabbix

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

def read_csv(file_path):
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(f"Lendo linha do CSV: {row}")  # Mensagem de depuração
                yield row
    except FileNotFoundError as e:
        print(f"Arquivo CSV não encontrado: {e}")
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")

def authenticate_zabbix(user, password):
    # Requisição de autenticação para obter o token
    auth_response = zabbix_request('user.login', {
        'user': user,
        'password': password
    })
    if auth_response and 'result' in auth_response:
        return auth_response['result']
    else:
        print(f"Erro ao autenticar: {auth_response}")
        return None

try:
    # Autenticar e obter o token
    username = 'Admin'  # Substitua pelo seu nome de usuário
    password = 'zabbix'  # Substitua pela sua senha
    auth_token = authenticate_zabbix(username, password)
    if not auth_token:
        raise Exception("Não foi possível autenticar. Verifique as credenciais e a API do Zabbix.")

    # Solicitar o ID do hostgroup do usuário
    hostgroup_id = input("Digite o ID do hostgroup do Zabbix: ")

    # Solicitar o ID do template do usuário
    template_id = input("Digite o ID do template do Zabbix: ")

    contador = 0

    # Loop para criar hosts
    for i, data in enumerate(read_csv('ficha.csv'), 1):
        if not data:
            continue

        contador += 1

        # Mensagens de depuração para verificar os dados lidos
        print(f"Dados da linha {i}: {data}")

        try:
            # Verificar se as chaves esperadas estão presentes
            if 'Host name' not in data or 'IP' not in data or 'Descrição' not in data or 'SO ou Ativo de Rede' not in data:
                print("Colunas esperadas ausentes no CSV.")
                continue

            host_name = data['Host name']
            ip_address = data['IP']
            description = data['Descrição']
            so_or_network = data['SO ou Ativo de Rede']

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
                }, auth_token=auth_token)

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
                }, auth_token=auth_token)

            if host_create_response:
                if 'result' in host_create_response:
                    print(f"""
                    Host criado: {host_name},
                    IP Atribuído: {ip_address},
                    Descrição: {description},
                    SO ou Ativo de Rede: {so_or_network}""")
                else:
                    print(f"Erro ao criar host {host_name}: {host_create_response}")
            else:
                print(f"Resposta vazia ao tentar criar o host {host_name}")

        except KeyError as e:
            print(f"Erro de chave ao processar o host {host_name}: {e}")
            contador -= 1
        except Exception as e:
            print(f"Erro ao criar host {host_name}: {e}")
            contador -= 1

    print(f"Número de novos Hosts criados: {contador}")

except Exception as e:
    print(f"Erro geral: {e}")

finally:
    # Logout após criar os hosts (opcional)
    # Se você não deseja fazer logout, pode comentar ou remover esta parte.
    try:
        logout_response = zabbix_request('user.logout', {}, auth_token=auth_token)
        if logout_response and 'result' in logout_response:
            print("Logout realizado com sucesso.")
        else:
            print(f"Erro ao fazer logout: {logout_response}")
    except Exception as e:
        print(f"Erro ao tentar fazer logout: {e}")
