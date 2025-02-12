import requests
from requests.auth import HTTPBasicAuth
import sys

# Verificar se todos os parâmetros foram passados
if len(sys.argv) != 4:
    print("Uso correto: python seu_script.py <username> <password> <nsx_manager>")
    sys.exit(1)

# Configurações (a partir dos parâmetros de linha de comando)
USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
NSX_MANAGER = sys.argv[3]

# Endpoints para métricas
URL_NODES = f"{NSX_MANAGER}/api/v1/transport-nodes"
URL_NETWORK_METRICS = f"{NSX_MANAGER}/api/v1/transport-nodes/{{node_id}}/metrics/network"
URL_CPU_METRICS = f"{NSX_MANAGER}/api/v1/transport-nodes/{{node_id}}/metrics/cpu"
URL_MEMORY_METRICS = f"{NSX_MANAGER}/api/v1/transport-nodes/{{node_id}}/metrics/memory"

# Desativar warnings de SSL (caso não tenha um certificado válido)
requests.packages.urllib3.disable_warnings()

# Autenticação
auth = HTTPBasicAuth(USERNAME, PASSWORD)

# Cabeçalhos
headers = {
    "Accept": "application/json"
}

# Função para obter as métricas de rede
def get_network_metrics(node_id):
    network_url = URL_NETWORK_METRICS.format(node_id=node_id)
    response = requests.get(network_url, auth=auth, headers=headers, verify=False)
    
    if response.status_code == 200:
        network_data = response.json()
        network_traffic_rate = network_data.get("traffic_rate", "N/A")
        network_tx_rate = network_data.get("tx_rate", "N/A")
        network_rx_rate = network_data.get("rx_rate", "N/A")
        network_packets_drop = network_data.get("packets_drop", "N/A")
        return network_traffic_rate, network_tx_rate, network_rx_rate, network_packets_drop
    else:
        print(f"Erro ao obter dados de rede para o node {node_id}: {response.status_code}")
        return None, None, None, None

# Função para obter as métricas de CPU
def get_cpu_metrics(node_id):
    cpu_url = URL_CPU_METRICS.format(node_id=node_id)
    response = requests.get(cpu_url, auth=auth, headers=headers, verify=False)
    
    if response.status_code == 200:
        cpu_data = response.json()
        cpu_usage_rate = cpu_data.get("cpu_usage_rate", "N/A")
        return cpu_usage_rate
    else:
        print(f"Erro ao obter dados de CPU para o node {node_id}: {response.status_code}")
        return None

# Função para obter as métricas de memória
def get_memory_metrics(node_id):
    memory_url = URL_MEMORY_METRICS.format(node_id=node_id)
    response = requests.get(memory_url, auth=auth, headers=headers, verify=False)
    
    if response.status_code == 200:
        memory_data = response.json()
        memory_usage_rate = memory_data.get("memory_usage_rate", "N/A")
        return memory_usage_rate
    else:
        print(f"Erro ao obter dados de memória para o node {node_id}: {response.status_code}")
        return None

# Requisição GET para os nodes
response = requests.get(URL_NODES, auth=auth, headers=headers, verify=False)

# Verifica resposta
if response.status_code == 200:
    print("NSX-T Edge Nodes encontrados:")
    data = response.json()
    
    for node in data.get("results", []):
        if node.get("node_deployment_info", {}).get("resource_type") == "EdgeNode":
            node_name = node.get('display_name')
            node_id = node.get('id')
            print(f"- Nome: {node_name}")
            print(f"  ID: {node_id}")
            print(f"  Estado: {node.get('host_switch_spec', {}).get('resource_type')}")
            
            # Obter as métricas
            network_traffic_rate, network_tx_rate, network_rx_rate, network_packets_drop = get_network_metrics(node_id)
            cpu_usage_rate = get_cpu_metrics(node_id)
            memory_usage_rate = get_memory_metrics(node_id)
            
            # Exibir as métricas
            print(f"  Network Traffic Rate: {network_traffic_rate}")
            print(f"  Network TX Rate: {network_tx_rate}")
            print(f"  Network RX Rate: {network_rx_rate}")
            print(f"  Network Packets Drop: {network_packets_drop}")
            print(f"  CPU Usage Rate: {cpu_usage_rate}")
            print(f"  Memory Usage Rate: {memory_usage_rate}")
            print("\n")
else:
    print(f"Erro: {response.status_code} - {response.text}")
