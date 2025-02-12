import requests
from requests.auth import HTTPBasicAuth

# Configurações
NSX_MANAGER = "https://seu-nsx-manager"
USERNAME = "admin"
PASSWORD = "sua-senha"

# Endpoint para listar os transport nodes (inclui Edge Nodes)
URL_NODES = f"{NSX_MANAGER}/api/v1/transport-nodes"
URL_CPU = f"{NSX_MANAGER}/api/v1/transport-nodes/{{node_id}}/metrics/cpu"  # Supondo que exista esse endpoint

# Desativar warnings de SSL (caso não tenha um certificado válido)
requests.packages.urllib3.disable_warnings()

# Autenticação
auth = HTTPBasicAuth(USERNAME, PASSWORD)

# Cabeçalhos
headers = {
    "Accept": "application/json"
}

# Função para obter informações de CPU
def get_cpu_rate(node_id):
    cpu_url = URL_CPU.format(node_id=node_id)
    response = requests.get(cpu_url, auth=auth, headers=headers, verify=False)
    
    if response.status_code == 200:
        cpu_data = response.json()
        # Exemplo de como pegar a taxa de CPU, ajuste conforme a estrutura real do JSON de resposta
        cpu_rate = cpu_data.get("cpu_rate", "N/A")
        return cpu_rate
    else:
        print(f"Erro ao obter dados de CPU para o node {node_id}: {response.status_code}")
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
            
            # Obter informações de CPU
            cpu_rate = get_cpu_rate(node_id)
            if cpu_rate:
                print(f"  Taxa de CPU: {cpu_rate}")
            print("\n")
else:
    print(f"Erro: {response.status_code} - {response.text}")
