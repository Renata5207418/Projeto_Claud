from typing import Optional
from google.api_core.client_options import ClientOptions
from google.cloud import documentai
from config.settings import settings


def process_document(
        project_id: str,
        location: str,
        processor_id: str,
        file_path: str,
        mime_type: str,
        field_mask: Optional[str] = None,
        processor_version_id: Optional[str] = None) -> dict:
    """
    Processa um documento através do Document AI e retorna um dicionário de entidades.

    Parâmetros:
      project_id            – ID do projeto GCP
      location              – região do serviço (ex.: "us", "eu")
      processor_id          – ID do processor configurado no Document AI
      file_path             – caminho local para o arquivo a processar
      mime_type             – tipo MIME do documento (ex.: "application/pdf")
      field_mask (opcional) – máscara de campos para limitar atributos retornados
      processor_version_id  – ID da versão específica do processor (fallback para a versão padrão se None)

    Fluxo:
      1. Configura ClientOptions apontando para o endpoint regional e credenciais ADC.
      2. Instancia DocumentProcessorServiceClient com essas opções.
      3. Monta o resource name:
         • Se `processor_version_id` fornecido, usa processor_version_path()
         • Caso contrário, usa processor_path()
      4. Lê todo o conteúdo do arquivo em bytes.
      5. Cria RawDocument(content, mime_type).
      6. Configura ProcessOptions:
         - individual_page_selector: páginas listadas em settings.page_selector
      7. Monta ProcessRequest(name, raw_document, field_mask, process_options).
      8. Chama client.process_document() e obtém result.document.entities.
      9. Converte a lista de entidades em dict:
         - chave = entity.type_
         - valor = mention_text (ou lista de mention_texts se houver múltiplas)
      10. Retorna esse dict de entidades.

    Retorno:
      dict onde cada chave é um tipo de entidade e o valor é:
        • string (se única ocorrência)
        • list[str] (se múltiplas ocorrências)
    """
    opts = ClientOptions(
        api_endpoint=f"{location}-documentai.googleapis.com",
        credentials_file=str(settings.google_application_credentials)
    )
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    if processor_version_id:
        name = client.processor_version_path(project_id, location, processor_id, processor_version_id)
    else:
        name = client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as image:
        image_content = image.read()

    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)

    process_options = documentai.ProcessOptions(
        individual_page_selector=documentai.ProcessOptions.IndividualPageSelector(pages=settings.page_selector)
    )

    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
        field_mask=field_mask,
        process_options=process_options,
    )

    result = client.process_document(request=request)
    document = result.document
    entities = document.entities

    entities_dict = {}
    for entity in entities:
        if entity.type_ in entities_dict:
            if not isinstance(entities_dict[entity.type_], list):
                entities_dict[entity.type_] = [entities_dict[entity.type_]]
            entities_dict[entity.type_].append(entity.mention_text)
        else:
            entities_dict[entity.type_] = entity.mention_text

    return entities_dict
