"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the conversational
retrieval graph. It includes the main graph definition, state management,
and key functions for processing & routing user queries, generating research plans to answer user questions,
conducting research, and formulating responses.
"""
from langchain_core.messages import HumanMessage
import asyncio

from langchain_core.messages import ToolMessage
from typing import Any, Literal, TypedDict, cast
from langchain_core.tools import StructuredTool

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph, MessagesState
from configuration import AgentConfiguration
from state import AgentState, InputState, Router
from langchain_core.language_models import BaseChatModel
from langchain_aws import ChatBedrock
from tools import tools, semantic_search_tool 


def load_chat_model() -> BaseChatModel:
    return ChatBedrock(
    model="anthropic.claude-3-haiku-20240307-v1:0",
    # other params...
)


async def analyze_and_route_query(
    state: AgentState, 
) -> dict[str, Router]:
    """Analiza la consulta del usuario y determina la ruta apropiada.

    Esta función utiliza un modelo de lenguaje para clasificar la consulta del usuario y decidir cómo dirigirla
    dentro del flujo de la conversación.

    Argumentos:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación.
        config (RunnableConfig): Configuración con el modelo utilizado para el análisis de la consulta.

    Retorna:
        dict[str, Router]: Un diccionario que contiene la clave 'router' con el resultado de la clasificación
                            (tipo de clasificación y lógica).
    """
    configuration = AgentConfiguration
    model = load_chat_model()
    print("estamos en el nodo: analyze_and_route_query")
    messages = [
        {"role": "system", "content": configuration.router_system_prompt}
    ] + state.messages

    response = await cast(
        Router, model.with_structured_output(Router).ainvoke(messages)
    )

    return {"router": response}


def route_query(
    state: AgentState,
) -> Literal["technical_retriever", "ask_for_more_info", "semantic_search", "respond_to_question_with_same_context"]:
    """Determine the next step based on the query classification.

    Args:
        state (AgentState): The current state of the agent, including the router's classification.

    Returns:
       Literal["technical_retriever", "ask_for_more_info", "semantic_search", "respond_to_question_with_same_context"]: The next step to take.

    Raises:
        ValueError: If an unknown router type is encountered.
    """

    print("estamos en el nodo: route_query")
    print(state.router["type"])
    return state.router["type"]



async def ask_for_more_info(
    state: AgentState,
): #-> dict[str, list[BaseMessage]]:
    """Genera una respuesta pidiendo más detalles al usuario sobre sus necesidades específicas.

    Este nodo se activa cuando el enrutador determina que se necesita más información del usuario.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """

    configuration = AgentConfiguration
    model = load_chat_model()
    #system_prompt = configuration.more_info_system_prompt.format(logic=state.router["logic"])
    system_prompt = configuration.more_info_system_prompt
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    #print(response)
    #return {"messages": [{"role": "assistant", "content": "ask_for_more_info"}]}

    return {"messages": [response]}



async def semantic_search(
    state: AgentState,
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta a una consulta abierta, por ejemplo que películas le recomendaría para café o carnes.

    Este nodo se activa cuando el enrutador clasifica la consulta como una pregunta general.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """

    configuration = AgentConfiguration
    model = load_chat_model()
    model_with_tools = model.bind_tools(tools, tool_choice = "semantic_search_tool")
    system_prompt = configuration.general_system_prompt
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    ai_msg = await model_with_tools.ainvoke(messages)
    return {"messages": [ai_msg]}
    #print(ai_msg)
    #query sise usa la api de converse
    #query = ai_msg.content[0]['input']['query']
    #print(type(ai_msg))
    #print(dir(ai_msg))  # Esto te mostrará los atributos disponibles de la clase

    tool_calls = ai_msg.tool_calls
    print("query:")
    query = tool_calls[0].get('args', {}).get('query', None)

    print(query)
    #print(tools)
    tool_output = semantic_search.invoke(query)
    tool_response = ToolMessage(content=tool_output,artifact=tool_output["items"], tool_call_id="semantic_search")
    #print("tool_response: ")
    #print(tool_response)
    #messages.append(tool_response)

    return {"messages": [tool_response]}

async def semantic_retriever(
    state: AgentState,
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta a una consulta abierta, por ejemplo que películas le recomendaría para café o carnes.

    Este nodo se activa cuando el enrutador clasifica la consulta como una pregunta general.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """

    #print(ai_msg)
    #query sise usa la api de converse
    #query = ai_msg.content[0]['input']['query']
    #print(type(ai_msg))
    #print(dir(ai_msg))  # Esto te mostrará los atributos disponibles de la clase

    query = state.messages[-1].tool_calls[0].get('args', {}).get('query', None)

    #print(tools)
    #tool_output = semantic_search.invoke(query)
    #print("query que debería encontrar en el tool response:")
    #print(query)
    #tool_call_id = state.messages[-1].tool_calls[0].get('id', {})
    #print(tool_call_id)

    #tool_response = ToolMessage(content=tool_output,tool_call_id=tool_call_id)
    #print("tool_response: ")
    #print(tool_response)
    #messages.append(tool_response)
    print("Recorriendo toll calls")
    for tool_call in state.messages[-1].tool_calls:
        selected_tool = {"semantic_search_tool": semantic_search_tool}[tool_call["name"].lower()]
        print("selected_tool: ")
        print(selected_tool)
        tool_msg = selected_tool.invoke(tool_call)
        print("tool_msg: ")
        print(tool_msg)
        return {"messages": [tool_msg]}



def respond_to_question_with_same_context(
    state: AgentState, 
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta a una consulta que puede ser respondida con el mismo contexto de los mensajes previos.

    Este nodo se activa cuando el enrutador clasifica la consulta como una pregunta contestable con el mismo contexto de los mensajes previos.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """

    configuration = AgentConfiguration
    model = load_chat_model()
    #system_prompt = configuration.general_system_prompt.format(logic=state.router["logic"])
    system_prompt = configuration.general_system_prompt
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    print("nodo: respond_to_question_with_same_context")
    response = model.ainvoke(messages)

    return {"messages": [response]}

def technical_retriever(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta a una consulta sobre una propiedad específica. dentro de la base de datos

    Este nodo se activa cuando el enrutador clasifica la consulta como una pregunta específica.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model()
    system_prompt = configuration.general_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    tool_response = model.ainvoke(messages)
    print("nodo: semantic_search")
    print(tool_response)
    return {"messages": [tool_response]}



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

async def respond(
    state: AgentState,
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta final a la consulta del usuario basándose en la investigación realizada.

    Este método formula una respuesta integral utilizando el historial de la conversación y los documentos obtenidos.

    Args:
        state (AgentState): El estado actual del agente, incluyendo los documentos recuperados y el historial de la conversación.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con la clave 'messages' que contiene la respuesta generada.
    """
    print("estamos en el nodo: respond")
    configuration = AgentConfiguration
    model = load_chat_model()
    model = model.bind_tools(tools)
    system_prompt = configuration.general_system_prompt    
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    print("messages: ")
    print(messages)
    save_to_txt(messages, "messages")
    response =  await model.ainvoke(messages)
    save_to_txt(response, "response")
    print(response)
    return {"messages": [response]}


# Define the graph
builder = StateGraph(MessagesState, config_schema=AgentConfiguration)
builder.add_node(analyze_and_route_query)
builder.add_node(ask_for_more_info)
builder.add_node(semantic_search)
builder.add_node(semantic_retriever)
builder.add_node(technical_retriever)
builder.add_node(respond_to_question_with_same_context)
builder.add_node(respond)

#define the flow
builder.add_edge(START, "analyze_and_route_query")
builder.add_conditional_edges("analyze_and_route_query", route_query)
#builder.add_edge("technical_retriever", "semantic_search","ask_for_more_info", "respond_to_question_with_same_context")

builder.add_edge("respond_to_question_with_same_context", END)
builder.add_edge("ask_for_more_info", END)
builder.add_edge("semantic_search", "semantic_retriever")
builder.add_edge("semantic_retriever", "respond")
builder.add_edge("technical_retriever", "respond")
builder.add_edge("respond", END)

# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "RetrievalGraph"

from IPython.display import Image, display

graph_data = graph.get_graph(xray=1).draw_mermaid_png()

# Guardar el gráfico como archivo PNG
with open('graph.png', 'wb') as f:
    f.write(graph_data)


async def main():
    #output = await graph.ainvoke({"messages": [HumanMessage(content="Cual es la mejor pelicula?")]})
    output = await graph.ainvoke({"messages": [HumanMessage(content="¿Cuál es el tipo de película me srive para empacar o envovler café?")]})

    #output["messages"][-1].pretty_print()  # output contains all messages in state
    for message in output["messages"]:
        message.pretty_print()

# Para ejecutarlo en un script normal
if __name__ == "__main__":
    asyncio.run(main())
