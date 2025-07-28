from google.cloud import pubsub_v1
import json
from google.api_core.exceptions import NotFound


def notificar_cloud3(os_id: int, pasta: str, topic_id: str, project_id: str):
    """
    Publica uma mensagem no tópico Pub/Sub do Cloud_3.

    Parâmetros:
      os_id      — identificador da OS que gerou “TOMADOS”
      pasta      — nome da pasta correspondente (ex.: "12345-CLIENTE")
      topic_id   — nome do tópico Pub/Sub (sem o prefixo "projects/.../topics/")
      project_id — ID do seu projeto GCP

    Formato da mensagem:
      {
        "os_id": <int>,
        "pasta": "<string>"
      }

    Comportamento:
      - Constrói o client PublisherClient()
      - Monta o full topic path com `publisher.topic_path()`
      - Serializa a mensagem como JSON e publica
      - Chama `future.result()` para aguardar confirmação de publicação

    Sugestões de melhoria:
      1. Usar um logger em vez de `print()` para não poluir stdout em produção.
      2. Incluir campos adicionais na mensagem (timestamp, ambiente, etc).
      3. Adicionar tratamento de erros/exceções para evitar falha silenciosa caso a publicação não ocorra.
      4. Para alto throughput, reutilizar o `PublisherClient()` em vez de criar um novo a cada chamada.
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    try:
        publisher.get_topic(request={"topic": topic_path})
    except NotFound:
        publisher.create_topic(name=topic_path)
    mensagem = {
        "os_id": os_id,
        "pasta": pasta
    }
    # Dica: pode adicionar outros campos se precisar (timestamp, etc)
    future = publisher.publish(topic_path, json.dumps(mensagem).encode("utf-8"))
    future.result()  # Aguarda publicar
    print(f"[Cloud_2] Mensagem enviada para o tópico {topic_id} ({project_id}): {mensagem}")
