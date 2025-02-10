import csv
import requests
import json
import warnings
import os

# Desabilita os warnings relacionados a SSL
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# URL da API do Zabbix e token de autenticação
url = "http://192.168.0.20/zabbix/api_jsonrpc.php"
token = "f3a71968429c5e6841a40581c9908a16110aa720a60b63acb695501facd2bbd4"

# Cabeçalhos da requisição
headers = {
    "Content-Type": "application/json"
}

# Arquivos de log
sucesso_log = "sucesso.log"
erro_log = "erro.log"

# Cria/limpa os arquivos de log
open(sucesso_log, "w").close()
open(erro_log, "w").close()

def call_zabbix_api(method, params):
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": token,
            "id": 1
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        return response.json()
    except Exception as e:
        print(f"❌ Erro na requisição {method}: {str(e)}")
        return None

def log_result(filename, message):
    with open(filename, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

# Lendo o arquivo CSV
with open("hosts.csv", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")
    for row in reader:
        try:
            host_name = row["Nome"]
            print(f"\n🔍 Processando host: {host_name}")

            # Buscar o host usando output extend para trazer todas as infos, inclusive as tags existentes
            host_params = {
                "output": "extend",
                "search": {"name": host_name},
                "searchWildcardsEnabled": True
            }
            host_response = call_zabbix_api("host.get", host_params)
            if not host_response or "result" not in host_response or not host_response["result"]:
                err = f"❌ Host não encontrado: {host_name}"
                print(err)
                log_result(erro_log, err)
                continue

            host = host_response["result"][0]
            host_id = host["hostid"]
            print(f"✅ Host encontrado: {host_name} (ID: {host_id})")

            # Obter grupos atuais do host
            current_groups_params = {"output": ["groupid"], "hostids": host_id}
            current_groups_response = call_zabbix_api("hostgroup.get", current_groups_params)
            current_group_ids = [{"groupid": g["groupid"]} for g in current_groups_response.get("result", [])]

            # Criar os novos grupos a partir das colunas
            fabricante = row["Fabricante"].upper()
            ambiente = row["Ambiente"].upper()
            subambiente = row["Subambiente"].upper()

            new_host_groups = list(set([
                fabricante,
                f"{fabricante}_{ambiente}",
                f"{fabricante}_{ambiente}_{subambiente}"
            ]))

            new_group_ids = []
            for group_name in new_host_groups:
                group_params = {"output": ["groupid"], "filter": {"name": [group_name]}}
                group_response = call_zabbix_api("hostgroup.get", group_params)
                if group_response and "result" in group_response and group_response["result"]:
                    group_id = group_response["result"][0]["groupid"]
                else:
                    # Criar grupo se não existir
                    create_group_params = {"name": group_name}
                    create_group_response = call_zabbix_api("hostgroup.create", create_group_params)
                    if create_group_response and "result" in create_group_response:
                        group_id = create_group_response["result"]["groupids"][0]
                    else:
                        err = f"❌ Erro ao criar grupo: {group_name}"
                        print(err)
                        log_result(erro_log, err)
                        continue
                if {"groupid": group_id} not in new_group_ids:
                    new_group_ids.append({"groupid": group_id})

            # Unir os grupos atuais com os novos (evitando duplicatas)
            all_group_ids = {g["groupid"]: g for g in current_group_ids + new_group_ids}.values()

            # Obter as tags atuais do host (já disponíveis com output extend)
            current_tags = host.get("tags", [])
            
            # Criar as novas tags conforme solicitado
            new_tags = [
                {"tag": "TIPO", "value": f"{row['Tipo'].upper()} {row['Fabricante'].upper()}"},
                {"tag": "MODELO", "value": row["Modelo"].upper()},
                {"tag": "AMBIENTE", "value": row["Ambiente"].upper()},
                {"tag": "LOCALIDADE", "value": row["Localidade"].upper()},
                {"tag": "SUBAMBIENTE", "value": row["Subambiente"].upper()}
            ]
            
            # Combinar as tags atuais com as novas, removendo duplicatas (baseado na tupla (tag, value))
            tag_map = {(tag["tag"], tag["value"]): tag for tag in current_tags + new_tags}
            all_tags = list(tag_map.values())

            # Atualizar o host mantendo os grupos e tags existentes e adicionando os novos
            update_params = {
                "hostid": host_id,
                "groups": list(all_group_ids),
                "tags": all_tags
            }
            update_response = call_zabbix_api("host.update", update_params)

            if update_response and "result" in update_response:
                success_msg = f"✅ Host {host_name} atualizado com sucesso!"
                print(success_msg)
                log_result(sucesso_log, success_msg)
            else:
                err = f"❌ Erro ao atualizar host {host_name}"
                print(err)
                log_result(erro_log, err)

        except Exception as e:
            err = f"❌ Erro inesperado ao processar {host_name}: {str(e)}"
            print(err)
            log_result(erro_log, err)
 