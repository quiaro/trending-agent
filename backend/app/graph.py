"""LangGraph implementation for trending information retrieval."""
import os
from typing import Dict, List, TypedDict, Annotated, Sequence, Union, cast
import operator
import json
import sys
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from langchain_core.tools import BaseTool
from app.tools import google_trends, google_search, reddit_search

# Define the state schema
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]], add_messages]

# Define the available tools
tools = [google_trends, google_search, reddit_search]

# Define the system message
system_message = SystemMessage(
    content="""You are a helpful assistant that provides trending information.
    You have access to tools that can help you find trending information on a
    specific topic. Use these tools to provide comprehensive answers."""
)

# Define the agent node
def agent(state: AgentState) -> Dict:
    """
    Agent node that processes messages and decides next steps.
    
    Args:
        state: The current state with messages
        
    Returns:
        Updated state with new messages and potential next node
    """
    messages = state["messages"]
    
    # Prepare messages for the model
    model_messages = []
    if not any(isinstance(m, SystemMessage) for m in messages):
        model_messages.append(system_message)
    
    model_messages.extend(messages)
    
    # Call the OpenAI model
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system" if isinstance(m, SystemMessage) else
                   "user" if isinstance(m, HumanMessage) else
                   "assistant" if isinstance(m, AIMessage) else
                   "function", 
            "content": m.content if not isinstance(m, FunctionMessage) else None,
            "name": m.name if isinstance(m, FunctionMessage) else None,
            "function_call": m.additional_kwargs.get("function_call", None) 
                  if isinstance(m, AIMessage) else None
        } for m in model_messages if m.content is not None or isinstance(m, FunctionMessage)],
        tools=[{
            "type": "function",
            "function": {
                "name": tool.name if isinstance(tool, BaseTool) else tool.__name__,
                "description": tool.description if isinstance(tool, BaseTool) else tool.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        } for tool in tools],
        stream=False
    )
    
    # Process the response
    message = response.choices[0].message
    
    # Convert to LangChain message format
    if hasattr(message, "tool_calls") and message.tool_calls:
        tool_call = message.tool_calls[0]
        ai_message = AIMessage(
            content=message.content or "",
            tool_calls=[{
                "name": tool_call.function.name,
                "args": json.loads(tool_call.function.arguments),
                "id": tool_call.id
            }]
        )
    else:
        ai_message = AIMessage(content=message.content or "")
    
    # Add to messages
    new_messages = messages + [ai_message]
    
    return {"messages": new_messages}

# Define a conditional edge to check if we should continue
def should_continue(state: AgentState) -> str:
    """
    Determine if the agent should continue to tools or end.
    
    Args:
        state: Current state with messages
        
    Returns:
        Next node to route to
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if the last message is a tool call
    if (
        isinstance(last_message, AIMessage) and 
        hasattr(last_message, "tool_calls") and 
        last_message.tool_calls
    ):
        return "tool_selector"
    
    return END

# Create the tool selector node
tool_node = ToolNode(tools=[google_trends, google_search, reddit_search])

# Define the tool selector node function
def tool_selector(state: AgentState) -> Dict:
    """
    Select and execute the appropriate tool based on the agent's request.
    
    Args:
        state: Current state with messages
        
    Returns:
        Updated state with tool execution results
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Extract tool call details
    if (
        isinstance(last_message, AIMessage) and 
        hasattr(last_message, "tool_calls") and 
        last_message.tool_calls
    ):
        tool_call = last_message.tool_calls[0]
        function_name = tool_call["name"]
        arguments = tool_call["args"]
        
        # Execute the specified tool
        result = None
        for tool in tools:
            tool_name = tool.name if isinstance(tool, BaseTool) else tool.__name__
            if tool_name == function_name:
                # Use tool.invoke() instead of tool(**arguments) for BaseTool instances
                if isinstance(tool, BaseTool):
                    result = tool.invoke(arguments)
                else:
                    result = tool(**arguments)
                break
        
        if result:
            # Add function message with result
            function_message = FunctionMessage(
                content=result,
                name=function_name,
                tool_call_id=tool_call.get("id", "")
            )
            return {"messages": messages + [function_message]}
    
    return {"messages": messages}

# Build the graph
def build_graph() -> StateGraph:
    """
    Build and return the LangGraph for trending information retrieval.
    
    Returns:
        A configured StateGraph
    """
    # Create the workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent)
    workflow.add_node("tool_selector", tool_selector)
    
    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tool_selector": "tool_selector",
            END: END
        }
    )
    workflow.add_edge("tool_selector", "agent")
    
    # Set the entry point
    workflow.set_entry_point("agent")
    
    return workflow

# Create the graph instance
graph = build_graph().compile() 