#!/bin/bash
set -e # Exit on any error

echo "🚀 =========================================="
echo "🚀 Starting Bulletproof A2A + MCP Demo"
echo "🚀 =========================================="

# 1. Ensure we are in the right directory and venv is active
cd "$(dirname "$0")"
source .venv/bin/activate

echo "🧹 Step 1: Cleaning up any stale background processes..."
pkill -f "order-agent.py" || true
pkill -f "inventory-agent.py" || true
pkill -f "cart_agent.py" || true
sleep 1 # Give OS time to release file descriptors

echo "🗑️  Step 2: Deleting old trace logs (Critical for clean state)..."
rm -f trace.log eval_results.json

echo "⚙️  Step 3: Starting fresh A2A Agents in background..."
python order-agent.py > agent_order.log 2>&1 &
ORDER_PID=$!
python inventory-agent.py > agent_inventory.log 2>&1 &
INVENTORY_PID=$!
python cart_agent.py > agent_cart.log 2>&1 &
CART_PID=$!

echo "⏳ Step 4: Waiting 3 seconds for Uvicorn servers to bind ports..."
sleep 3

echo "✅ Agents started! (PIDs: Order=$ORDER_PID, Inventory=$INVENTORY_PID, Cart=$CART_PID)"
echo "🧪 Step 5: Running the Automated Eval Harness..."
echo "----------------------------------------"
python run_evals.py
echo "----------------------------------------"

echo "🎉 Demo environment is now live and stable!"
echo "💡 Tip: You can now run 'python supervisor.py' for live interactive chat."
echo "💡 Tip: To stop background agents later, run: pkill -f 'agent.py'"

