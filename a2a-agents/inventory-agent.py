import asyncio
import uvicorn
from starlette.applications import Starlette

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_jsonrpc_routes, create_agent_card_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import a2a_pb2

from common import build_agent, LangChainAgentExecutor

PORT = 9102

card = a2a_pb2.AgentCard(
    name="Inventory Agent",
    description="Product search and stock questions.",
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
        id="inventory", name="Inventory",
        description="Search products by name and check stock levels.",
        tags=["inventory"], examples=["Do you have wireless mice?"])],
)


async def make_app():
    trace_id_holder = {}
    agent = await build_agent(
        ["searchProducts", "checkInventory"],
        "You handle product search and stock questions. Follow these strict rules:\n"
        "RULE 1: If the user provides a product NAME or plural form (e.g., 'mouse', 'mice', 'keyboard', 'laptops'), you MUST call `searchProducts` with that name as the query. NEVER call `checkInventory` for name-based queries, because it requires a numeric productId that the user did not provide.\n"
        "RULE 2: Only call `checkInventory` if the user explicitly provides a numeric productId (e.g., 'product 1' or 'ID 5').\n"
        "For queries like 'how much stock of mouse', treat 'mouse' as the product name and call searchProducts(query='mouse').",
        trace_id_holder)
    handler = DefaultRequestHandler(
        agent_executor=LangChainAgentExecutor(agent,trace_id_holder),
        task_store=InMemoryTaskStore(),
        agent_card=card)
    routes = create_jsonrpc_routes(handler, rpc_url="/rpc") + create_agent_card_routes(card)
    return Starlette(routes=routes)


if __name__ == "__main__":
    app = asyncio.run(make_app())
    uvicorn.run(app, host="0.0.0.0", port=PORT)