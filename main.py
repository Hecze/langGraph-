import boto3
import re
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain_aws import ChatBedrockConverse
import retrieval_graph.tools as tools

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('obenGroup_films')

def save_to_txt(data, filename: str):
    """Guardar los datos tal cual en un archivo txt."""
    # Convertir el dato a string si no es string (esto es para asegurar que todo se pueda guardar en el archivo)
    data_str = str(data)
    
    # Definir la ruta del archivo .txt
    file_path = f"./{filename}.txt"
    
    # Guardar el archivo en formato texto
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(data_str)
    
    print(f"El contenido se ha guardado en {file_path}")



# Ejemplo de uso de la función semantic_search
if __name__ == '__main__':
    query = "¿Qué películas se puede usar para empacar o envolver café?"
    
    result = tools.semantic_search.invoke(query)
    print("Resultado:", result)
