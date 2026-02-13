import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


def get_github_client():
    token = os.getenv("GH_TOKEN", None)
    if not token:
        print("Erro: A variável de ambiente GH_TOKEN não está definida.", flush=False)
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return headers


def test_connection():
    url = "https://api.github.com/graphql"
    headers = get_github_client()

    query = """
        query {
        viewer {
            login
            name
            url
        }
    }
    """

    try:
        response = requests.post(
            url, json={"query": query}, headers=headers, timeout=10
        )
        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict) and "errors" in data:
            print("Erro na consulta GraphQL:", data["errors"], flush=False)
        elif isinstance(data, dict):
            print("Conexão bem-sucedida! Dados do usuário:", flush=False)
            print("Login:", data["data"]["viewer"]["login"], flush=False)
            print("Nome:", data["data"]["viewer"]["name"], flush=False)
            print("URL:", data["data"]["viewer"]["url"], flush=False)

    except requests.exceptions.RequestException as e:
        print("Erro na conexão com a API do GitHub:", e, flush=False)


if __name__ == "__main__":
    test_connection()
