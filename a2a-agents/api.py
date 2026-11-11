from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time
import json

from supervisor import route, ask, ask_both, AGENTS
from tracing import new_trace_id

app = FastAPI(title="E-Commerce Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    routing_target: str
    routing_display: str
    trace_id: str
    tools_called: list[str]
    latency_ms: float
    is_fanout: bool

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/agents")
async def list_agents():
    return {
        "agents": [
            {"name": "order_agent", "port": 9101, "url": AGENTS["order"]},
            {"name": "inventory_agent", "port": 9102, "url": AGENTS["inventory"]},
            {"name": "cart_agent", "port": 9103, "url": AGENTS["cart"]},
        ]
    }

def extract_text_from_response(raw_response: str) -> str:
    """Extract the actual text from the protobuf string representation, handling fan-out."""
    try:
        import re
        # Find ALL text fields in the protobuf string(s)
        matches = re.findall(r'text:\s*"([^"]*)"', raw_response)
        if matches:
            # If there are multiple matches (e.g., from fan-out), join them cleanly
            return "\n\n".join(matches)
        else:
            return raw_response
    except Exception:
        return raw_response

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    t0 = time.time()
    trace_id = new_trace_id()
    text = req.message
    
    target = route(text)
    is_fanout = (target == "both")
    
    # Determine display text
    if is_fanout:
        routing_display = "Fan-out: Order Agent + Inventory Agent (parallel)"
    else:
        agent_names = {
            "order": "Order Agent",
            "inventory": "Inventory Agent",
            "cart": "Cart Agent"
        }
        routing_display = f"Routed to {agent_names.get(target, target)}"
    
    # Call the appropriate agent(s)
    if is_fanout:
        raw_result = await ask_both(text, trace_id)
    else:
        raw_result = await ask(AGENTS[target], text, trace_id)
    
    latency_ms = (time.time() - t0) * 1000
    
    # Extract clean text from protobuf response
    response_text = extract_text_from_response(raw_result)
    
    # Parse tools_called from trace.log
    tools_called = []
    try:
        with open("trace.log") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if event.get("trace_id") == trace_id and event.get("span") == "mcp.tool_call":
                        tools_called.append(event.get("tool"))
                except:
                    continue
    except FileNotFoundError:
        pass
    
    return ChatResponse(
        response=response_text,
        routing_target=target,
        routing_display=routing_display,
        trace_id=trace_id,
        tools_called=tools_called,
        latency_ms=latency_ms,
        is_fanout=is_fanout
    )