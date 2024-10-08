import csv
import requests
import json

# Configurações do Zabbix
zabbix_url = 'http://192.168.3.10/zabbix/api_jsonrpc.php'  # Use 'https' se o servidor suportar HTTPS
auth_token = 'seu_token_aqui'  # Substitua pelo seu token de autenticação

def zabbix_request(method, params):
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
        if 'error' in response_data:
            error_message = f"Erro na resposta da API: {response_data['error']}"
            print(error_message)
            log_error(params.get('host', 'Desconhecido'), error_message)
        return response_data
    except requests.RequestException as e:
        error_message = f"Erro na requisição para Zabbix: {e}"
        print(error_message)
        log_error(params.get('host', 'Desconhecido'), error_message)
        return None
    except json.JSONDecodeError as e:
        error_message = f"Erro ao decodificar JSON da resposta: {e}"
        print(error_message)
        log_error(params.get('host', 'Desconhecido'), error_message)
        return None

def read_csv(file_path):
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')  # Ajuste para usar ponto e vírgula como delimitador
            for row in reader:
                print(f"Lendo linha do CSV: {row}")  # Mensagem de depuração
                yield row
    except FileNotFoundError as e:
        print(f"Arquivo CSV não encontrado: {e}")
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")

def log_error(host_name, error_message):
    with open('hosts.log', 'a') as log_file:
        log_file.write(f"Host: {host_name}, Erro: {error_message}\n")

try:
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
                raise ValueError("Colunas esperadas ausentes no CSV.")

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
                })

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
                })

            if host_create_response:
                if 'result' in host_create_response:
                    print(f"""
                    Host criado: {host_name},
                    IP Atribuído: {ip_address},
                    Descrição: {description},
                    SO ou Ativo de Rede: {so_or_network}""")
                else:
                    error_message = f"Erro ao criar host {host_name}: {host_create_response}"
                    print(error_message)
                    log_error(host_name, error_message)
            else:
                error_message = f"Resposta vazia ao tentar criar o host {host_name}"
                print(error_message)
                log_error(host_name, error_message)

        except KeyError as e:
            error_message = f"Erro de chave ao processar o host {host_name}: {e}"
            print(error_message)
            log_error(host_name, error_message)
            contador -= 1
        except Exception as e:
            error_message = f"Erro ao criar host {host_name}: {e}"
            print(error_message)
            log_error(host_name, error_message)
            contador -= 1

    print(f"Número de novos Hosts criados: {contador}")

except Exception as e:
    print(f"Erro geral: {e}")
