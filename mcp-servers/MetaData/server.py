from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from tools_metadata import metadata_mcp, get_social_media_comments

# Create your main FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "MCP SSE Server is running!"}

@app.post("/mcp/call")
async def call_endpoint(request: Request):
    body = await request.json()
    print(body)
    url = body["url"]
    doc_id = body["doc_id"]
    try:
        result = get_social_media_comments(url, doc_id)

        return JSONResponse({"status": "success", "result": result})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

# Mount the FastMCP SSE app under a subpath (e.g., /mcp)
app.mount("/mcp", metadata_mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
