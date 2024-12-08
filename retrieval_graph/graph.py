"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the conversational
retrieval graph. It includes the main graph definition, state management,
and key functions for processing & routing user queries, generating research plans to answer user questions,
conducting research, and formulating responses.
"""

from typing import Any, Literal, TypedDict, cast

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from retrieval_graph.configuration import AgentConfiguration
from retrieval_graph.state import AgentState, InputState, Router
from langchain_core.language_models import BaseChatModel
from langchain.chat_models import init_chat_model
from langchain_aws import ChatBedrockConverse
from tools import tools


def load_chat_model() -> BaseChatModel:
    return ChatBedrockConverse(
    model="anthropic.claude-3-haiku-20240307-v1:0",
    temperature=0,
    max_tokens=None,
    # other params...
)


async def analyze_and_route_query(
    state: AgentState, *, config: RunnableConfig
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
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model()
    model.bind_tools(tools, tool_choice = "semantic_search")
    messages = [
        {"role": "system", "content": configuration.router_system_prompt}
    ] + state.messages

    response = cast(
        Router, await model.with_structured_output(Router).ainvoke(messages)
    )

    return {"router": response}


def route_query(
    state: AgentState,
) -> Literal["respond_to_technical_query", "ask_for_more_info", "respond_to_general_query", "respond_to_question_with_same_context"]:
    """Determine the next step based on the query classification.

    Args:
        state (AgentState): The current state of the agent, including the router's classification.

    Returns:
       Literal["respond_to_technical_query", "ask_for_more_info", "respond_to_general_query", "respond_to_question_with_same_context"]: The next step to take.

    Raises:
        ValueError: If an unknown router type is encountered.
    """
    _type = state.router["type"]
    if _type == "respond_to_technical_query":
        return "respond_to_technical_query"
    
    elif _type == "respond_to_general_query":
        return "respond_to_general_query"
    
    elif _type == "respond_to_question_with_same_context":
        return "respond_to_question_with_same_context"
    
    elif _type == "ask_for_more_info":
        return "ask_for_more_info"
    
    else:
        raise ValueError(f"Unknown router type {_type}")


async def ask_for_more_info(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta pidiendo más detalles al usuario sobre sus necesidades específicas.

    Este nodo se activa cuando el enrutador determina que se necesita más información del usuario.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model()
    system_prompt = configuration.more_info_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}



async def respond_to_general_query(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta a una consulta abierta, por ejemplo que películas le recomendaría para café o carnes.

    Este nodo se activa cuando el enrutador clasifica la consulta como una pregunta general.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.general_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}

async def respond_to_question_with_same_context(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta a una consulta que puede ser respondida con el mismo contexto de los mensajes previos.

    Este nodo se activa cuando el enrutador clasifica la consulta como una pregunta contestable con el mismo contexto de los mensajes previos.

    Args:
        state (AgentState): El estado actual del agente, incluyendo el historial de la conversación y la lógica del enrutador.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con una clave 'messages' que contiene la respuesta generada.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.general_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)

    return {"messages": [response]}

async def respond_to_technical_query(
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
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.general_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    tool_response = await model.ainvoke(messages)
    #Volvemos a llamar al modelo con la respuesta de la tool
    model = load_chat_model(configuration.query_model)
    messages = [{"role": "tool", "content": tool_response}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}




async def respond(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Genera una respuesta final a la consulta del usuario basándose en la investigación realizada.

    Este método formula una respuesta integral utilizando el historial de la conversación y los documentos obtenidos.

    Args:
        state (AgentState): El estado actual del agente, incluyendo los documentos recuperados y el historial de la conversación.
        config (RunnableConfig): Configuración con el modelo utilizado para responder.

    Returns:
        dict[str, list[str]]: Un diccionario con la clave 'messages' que contiene la respuesta generada.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.response_model)
    context = state.documents
    prompt = configuration.response_system_prompt.format(context=context)
    messages = [{"role": "system", "content": prompt}] + state.messages
    response = await model.ainvoke(messages)
    print(response)
    return {"messages": [response]}


# Define the graph
builder = StateGraph(AgentState, input=InputState, config_schema=AgentConfiguration)
builder.add_node(analyze_and_route_query)
builder.add_node(ask_for_more_info)
builder.add_node(respond_to_general_query)
builder.add_node(respond_to_technical_query)
builder.add_node(respond)

builder.add_edge(START, "analyze_and_route_query")
builder.add_conditional_edges("analyze_and_route_query", route_query)
builder.add_edge("respond_to_technical_query", "respond_to_general_query","ask_for_more_info", "respond_to_question_with_same_context")

builder.add_edge("ask_for_more_info", END)
builder.add_edge("respond_to_general_query", END)
builder.add_edge("respond_to_question_with_same_context", END)
builder.add_edge("respond_to_technical_query", END)
builder.add_edge("respond_to_general_query", END)
builder.add_edge("respond", END)

# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "RetrievalGraph"