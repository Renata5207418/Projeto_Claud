import os
import json
import logging
from google.cloud import pubsub_v1
from processa_tomados import processar_os_pubsub
from config.settings import settings
from google.api_core.exceptions import NotFound
from db.triage_consulta import get_tomados_status, set_tomados_concluido

PROJECT_ID = os.getenv("PROJECT_ID") or settings.gcloud_project_id
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID") or "cloud3-tomados-sub"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s"
)


def callback(message):
    """
        Função chamada a cada mensagem recebida da fila:
          - Decodifica e parseia JSON
          - Pula se tomados_status já for 'Concluído'
          - Processa via Cloud_3 (processar_os_pubsub)
          - Atualiza status no DB e faz ack
          - Em caso de exceção, faz nack para reentrega
    """
    try:
        data = json.loads(message.data.decode("utf-8"))
        os_id = data.get("os_id")
        pasta = data.get("pasta")
        logging.info(f"Recebido do Pub/Sub: os_id={os_id}, pasta={pasta}")

        # ── pule se já concluído ──
        if get_tomados_status(os_id) == "Concluído":
            logging.info("OS %s já concluída – ack direto.", os_id)
            message.ack()
            return

        # Processar
        processar_os_pubsub(os_id, pasta)
        # marca & ack
        set_tomados_concluido(os_id)
        message.ack()
        logging.info("OS %s processada com sucesso.", os_id)

    except Exception as e:
        logging.error("Erro no callback: %s", e, exc_info=True)
        message.nack()


def main():
    """
    Inicia o subscriber e trava em streaming_pull_future.result().
    Cancela a subscrição graciosamente em KeyboardInterrupt.
    """
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    try:
        subscriber.get_subscription(subscription_path)  # valida antes de escutar
    except NotFound:
        logging.error("Subscription %s não existe no projeto %s",
                      SUBSCRIPTION_ID, PROJECT_ID)
        return

    streaming_pull_future = subscriber.subscribe(subscription_path,
                                                 callback=callback)
    logging.info("Ouvindo em %s ... Ctrl+C para sair.", subscription_path)

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        logging.info("Encerrando o subscriber.")
    except Exception as e:
        logging.error("Subscriber falhou: %s", e, exc_info=True)
