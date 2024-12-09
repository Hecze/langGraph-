from langchain_core.tools import tool
from typing import Annotated, List
import boto3
import re
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
import logging
import decimal
from boto3.dynamodb.conditions import Key, Attr

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('obenGroup_films')

@tool
def specific_search_tool(
    FilmCodes: Annotated[List[str], "códigos o categorías de películas plásticas de ObenGroup para recuperar información. Los ejemplos incluyen ['CC 60', 'CWC 20', 'SCx 30'] para códigos o ['CC', 'CWC', 'SCx'] para los tipos."],
) -> dict:
    """Función de búsqueda específica y obtención de datos de DynamoDB."""
    try:
        def convert_decimals(obj):
            """Recursively convert DynamoDB Decimals to int or float for JSON serialization."""
            if isinstance(obj, list):
                return [convert_decimals(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, set):  # Agregado para manejar los sets
                return [convert_decimals(i) for i in obj]
            elif isinstance(obj, decimal.Decimal):
                return int(obj) if obj % 1 == 0 else float(obj)  # Convert to int if whole number, else to float
            else:
                return obj
        
        dynamodb_client = boto3.resource('dynamodb', region_name="us-east-1")
        films_table = dynamodb_client.Table('obenGroup_films')  # Tabla para buscar por características

        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        if isinstance(FilmCodes, list) and FilmCodes:
            # Crear un conjunto de códigos originales y sus versiones sin números
            FilmCodes_extended = set(FilmCodes)
            for code in FilmCodes:
                code_without_numbers = re.sub(r'\d+', '', code).strip()
                if code_without_numbers and code_without_numbers != code:
                    FilmCodes_extended.add(code_without_numbers)

            # Convertir el conjunto a una lista para evitar problemas de serialización
            FilmCodes_extended = list(FilmCodes_extended)
            print("Códigos de película con y sin números, búsqueda específica:")
            print(FilmCodes_extended)

            # Transformar cada string
            transformed_FilmCodes = [code.replace(" ", "").lower() for code in FilmCodes_extended]

            # Crear una sola expresión de filtro con in_
            final_filter_expression = Attr('id').is_in(transformed_FilmCodes)

            # Variable para almacenar los resultados finales
            all_items = []

            # Paginación de DynamoDB
            exclusive_start_key = None
            while True:
                if exclusive_start_key:
                    response = films_table.scan(
                        FilterExpression=final_filter_expression,
                        ExclusiveStartKey=exclusive_start_key
                    )
                else:
                    response = films_table.scan(
                        FilterExpression=final_filter_expression
                    )

                # Agregar los ítems recuperados
                all_items.extend(response.get('Items', []))

                # Verificar si hay más páginas
                if 'LastEvaluatedKey' in response:
                    exclusive_start_key = response['LastEvaluatedKey']
                else:
                    break

            #print("Todos los resultados recuperados:")
            #print(all_items)

            # Convertir los valores Decimal a tipos serializables
            all_items = convert_decimals({"Items": all_items})

            return  all_items.get("Items", []),
    
        else:
            return []

    except Exception as e:
        logger.error(f"Specific search error: {str(e)}")
        return None    

@tool
def semantic_search_tool(
    query: Annotated[str, "Frase a buscar en la base de datos semántica, por ejemplo: 'película que se puede usar para empacar o envolver café'."],
) -> dict:
    """Función maestra que integra todo el proceso de búsqueda semántica y obtención de datos de DynamoDB."""
    # Inicializa el retriever
    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id="2FHZ6TI9US",
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 5}},
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
    print("fuente_película_tipo: ")
    print(fuente_película_tipo)
    
    # 3. Obtener los items desde DynamoDB usando los IDs extraídos
    items_from_dynamo = fetch_items_from_dynamo(fuente_película_tipo)
    #
    # print("Query: " + query)
    #print("items from dynamo")
    #print(items_from_dynamo)
    # 4. Retornar un objeto con los items y el contador
    return items_from_dynamo


tools = [semantic_search_tool]
query = "película que sirve para empacar o envolver café"
tool_output = semantic_search_tool.invoke(query)
print(tool_output)
