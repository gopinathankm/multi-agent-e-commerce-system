import asyncio
import uvicorn
from starlette.applications import Starlette

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_jsonrpc_routes, create_agent_card_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import a2a_pb2

from common import build_agent, LangChainAgentExecutor

PORT = 9103

card = a2a_pb2.AgentCard(
    name="Cart Agent",
    description="Handles shopping cart operations: adding items, viewing cart, removing items, and checkout.",
    version="1.0.0",
    supported_interfaces=[a2a_pb2.AgentInterface(
        url=f"http://localhost:{PORT}/rpc",
        protocol_binding="JSONRPC",
        protocol_version="1.0",
    )],
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=a2a_pb2.AgentCapabilities(streaming=False),
    skills=[a2a_pb2.AgentSkill(
        id="cart_operations", name="Cart Operations",
        description="Add items to cart, view cart, remove items, and checkout.",
        tags=["cart", "checkout"], 
        examples=["Add 2 mice to my cart", "What's in my cart?", "Checkout please"])],
)

async def make_app():
    trace_id_holder = {}
    # Note: We include searchProducts so the agent can resolve product names to IDs before adding to cart
    agent = await build_agent(
        ["addToCart", "viewCart", "removeFromCart", "checkout", "searchProducts"],
        "You handle shopping cart operations. "
        "When the user wants to add a product by name (e.g., 'add mouse to cart'), you MUST first call searchProducts to find its productId, "
        "and then call addToCart with that productId and the requested quantity. "
        "When the user says 'checkout', call checkout. "
        "When the user asks what's in the cart, call viewCart. "
        "When the user wants to remove an item, call removeFromCart with the productId (use searchProducts first if only a name is given). "
        "Never guess a productId. Always use searchProducts to find it if the user provides a name.",
        trace_id_holder)
    
    handler = DefaultRequestHandler(
        agent_executor=LangChainAgentExecutor(agent, trace_id_holder),
        task_store=InMemoryTaskStore(),
        agent_card=card)
    
    routes = create_jsonrpc_routes(handler, rpc_url="/rpc") + create_agent_card_routes(card)
    return Starlette(routes=routes)

if __name__ == "__main__":
    app = asyncio.run(make_app())
    uvicorn.run(app, host="0.0.0.0", port=PORT)
