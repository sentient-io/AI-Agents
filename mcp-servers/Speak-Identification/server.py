from fastapi import FastAPI
import uvicorn
from tools_metadata import metadata_mcp

# Create your main FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "MCP SSE Server is running!"}

# Mount the FastMCP SSE app under a subpath (e.g., /mcp)
app.mount("/mcp", metadata_mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
