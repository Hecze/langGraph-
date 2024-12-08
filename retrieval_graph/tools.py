from langchain_core.tools import tool
from typing import Annotated, List
import boto3
import re
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('obenGroup_films')

@tool
def semantic_search(
    query: Annotated[str, "Frase a buscar en la base de datos semántica, por ejemplo: 'película que se puede usar para empacar o envolver café'."],
) -> dict:
    """Función maestra que integra todo el proceso de búsqueda semántica y obtención de datos de DynamoDB."""
    # Inicializa el retriever
    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id="2FHZ6TI9US",
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 10}},
    )

    def extract_uris(documents):
        """Extraer todos los URIs de los documentos y obtener los nombres entre '/' y '.json'."""
        uris = []
        names = []

        for doc in documents:
            # Obtener el URI del documento
            uri = doc.metadata['location']['s3Location']['uri']
            uris.append(uri)

            # Usar expresión regular para extraer el nombre entre '/' y '.json'
            match = re.search(r'\/([^\/]+)\.json$', uri)
            if match:
                names.append(match.group(1))  # Guardar el nombre extraído

        return names

    def fetch_items_from_dynamo(ids):
        """Obtener los items desde DynamoDB utilizando los IDs proporcionados."""
        items = []

        for item_id in ids:
            try:
                # Obtener el item de DynamoDB por ID (partition key)
                response = table.get_item(Key={'id': item_id})
                item = response.get('Item')  # La respuesta puede no tener un item si no se encuentra
                if item:
                    items.append(item)
            except Exception as e:
                print(f"Error al obtener el item con id {item_id}: {e}")

        return items
    
        # 1. Obtener la respuesta del retriever
    
    response = retriever.invoke(query)
    
    # 2. Extraer los IDs de los documentos (que están en los URIs)
    fuente_película_tipo = extract_uris(response)
    
    # 3. Obtener los items desde DynamoDB usando los IDs extraídos
    items_from_dynamo = fetch_items_from_dynamo(fuente_película_tipo)
    
    # 4. Retornar un objeto con los items y el contador
    return {
        "items": items_from_dynamo,
        "Count": len(items_from_dynamo)
    }

tools = [semantic_search]