"""FastAPI server for trending information retrieval."""
import os
import sys
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import build_graph, create_agent_state
from app.utils.setup import setup

# Call setup to initialize environment
setup()

graph = build_graph()
app = FastAPI(title="Trending Information API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Valid categories
VALID_CATEGORIES = [
    "Business and Finance",
    "Entertainment",
    "Food and Drink",
    "Games",
    "Health",
    "Hobbies and Leisure",
    "Jobs and Education",
    "Science",
    "Sports",
    "Technology"
]

async def stream_agent_response(category: str):
    """
    Stream the agent's response for a given category.
    
    Args:
        category: The trending category to query
        
    Yields:
        Chunks of the agent's response
    """
    # Create the initial prompt
    prompt = f"Find the top trending topic in the United States related to {category.lower()} and get the most relevant information related to this topic from Google and Reddit."
    
    # Initialize state
    state = create_agent_state(messages=[HumanMessage(content=prompt)])
    
    # Process through the graph
    try:
        async for chunk in graph.astream(state, stream_mode="updates"):
            for node, values in chunk.items():
                # Only yield messages from the agent
                if node == "agent":
                    last_message = values["messages"][-1].text()
                    if last_message != "":
                        yield last_message
                        yield "\n\n"

    except Exception as e:
        # Log the error but don't raise it to avoid breaking the stream
        print(f"Error in streaming response: {str(e)}")
        yield f"\n\nError during response generation: {str(e)}"


@app.get("/api/trending/{category}")
async def get_trending(
    category: str = Path(..., description="The category to get trending information for")
):
    """
    Get trending information for a specific category.
    
    Args:
        category: The category to get trending information for
        
    Returns:
        A streaming response with trending information
    """
    # Validate category
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
    # Return streaming response
    return StreamingResponse(
        stream_agent_response(category),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",  # Disable buffering for Nginx
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/api/categories")
async def get_categories():
    """
    Get the list of valid categories.
    
    Returns:
        List of valid categories
    """
    return {"categories": VALID_CATEGORIES}

if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    env = os.getenv("ENV", "development")
    
    # Only enable auto-reload in development
    reload = env.lower() == "development"
    
    uvicorn.run("app.main:app", host=host, port=port, reload=reload) 