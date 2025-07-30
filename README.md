# AI-Agents
AI Agents (n8n Flows &amp; MCP Servers)

## n8n
1. ASR
    1. ASR_Workflow.json (Create a new worflow in n8n then import this file.)

2. Elasticsearch
    1. ES_workflow.json (Create a new worflow in n8n then import this file.)

3. Wasabi
    1. Wasabi_WorkFlow.json (Create a new worflow in n8n then import this file.)

4. Action Agent
    1. ActionAgent_Workflow.json (Create a new worflow in n8n then import this file.)
    2. It have manage all MCP Servers tools.(ASR, Elasticsearch & Wasabi) 

## MCP-servers
1. ASR:

    Install depandence library.

    > pip install -r  mcp-servers/ASR/requirements.txt

    Run the server

    > python mcp-servers/ASR/server.py

2. Elasticsearch:

    Install depandence library.
    > pip install -r  mcp-servers/Elasticsearch/requirements.txt

    Run the server
    
    > python mcp-servers/Elasticsearch/server.py

3. Wasabi:

    Install depandence library.

    > pip install -r  mcp-servers/Wasabi/requirements.txt

    Run the server
    
    > python mcp-servers/Wasabi/server.py