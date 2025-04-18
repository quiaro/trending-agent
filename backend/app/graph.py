"""LangGraph implementation for trending information retrieval."""
import os
from typing import Dict, List, TypedDict, Annotated, Sequence, Union, cast
import operator
import json
import sys
from openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from langchain_core.tools import BaseTool
from app.tools import google_trends, google_search, reddit_search

model = ChatOpenAI(model="gpt-4o", temperature=0)

# Define the available tools
tools = [google_trends, google_search, reddit_search]

# Define the system message
system_message = SystemMessage(
    content="""You are a helpful assistant that provides trending information.
    You have access to tools that can help you find trending information on a
    specific topic. Use these tools to provide comprehensive answers."""
)


# Define the state schema
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]], add_messages]


# Define the agent node
def agent(state: AgentState) -> Dict:
    """
    Agent node that processes messages stored in the state.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with new messages returned from the tool selector node
    """
    messages = state["messages"]
    
    # Call OpenAI chat model
    response = model.invoke(messages)
    return {"messages": [response]}


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