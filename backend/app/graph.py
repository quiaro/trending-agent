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


# Factory function to create AgentState with system message
def create_agent_state(messages: List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]] = None) -> AgentState:
    all_messages = [system_message]
    if messages:
        all_messages.extend(messages)
    return AgentState(messages=all_messages)


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
    last_message = state["messages"][-1]
    
    # Check if the last message is a tool call
    if (
        isinstance(last_message, AIMessage) and 
        hasattr(last_message, "tool_calls")
    ):
        return "tool_selector"
    
    return END

# Create the tool selector node
tool_selector = ToolNode(tools=[google_trends, google_search, reddit_search])

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
        should_continue
    )
    workflow.add_edge("tool_selector", "agent")
    
    workflow.set_entry_point("agent")
    
    return workflow.compile()
