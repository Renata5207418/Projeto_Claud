import os
from google.cloud import storage

# Caminho da chave
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/usuario/PycharmProjects/Cloud_front/keys/credenciais_Cloud.json"

client = storage.Client()
bucket = client.bucket("claudio-tomados")
prefix = "tomados_saida"
blobs = list(bucket.list_blobs(prefix=prefix))

print("blobs encontrados:", [b.name for b in blobs])
