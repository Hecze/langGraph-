import boto3
import json
import os
from decimal import Decimal

# Función para convertir Decimal a float en el item (para DynamoDB)
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Tipo no serializable: {obj}")

# Crear el cliente de DynamoDB utilizando la librería de alto nivel
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('obenGroup_films')

# Directorio donde están los archivos JSON guardados
input_dir = './obenGroup_films'

# Función para cargar los datos de los archivos JSON a DynamoDB
def load_items_from_json():
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        # Asegurarse de que el archivo es un JSON y no un archivo erróneo
        if filename.endswith('.json'):
            try:
                # Leer el archivo JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    item = json.load(f)

                # Subir el item a DynamoDB
                response = table.put_item(
                    Item=item
                )
                print(f"Item con id {item.get('id')} cargado en DynamoDB.")
            except Exception as e:
                print(f"Error al cargar el archivo {filename}: {e}")

if __name__ == '__main__':
    # Cargar los items desde los archivos JSON a DynamoDB
    load_items_from_json()
