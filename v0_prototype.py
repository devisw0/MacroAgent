import os
import json
import ollama
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Initialize Alpaca
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# paper=True ensures we are using fake money!
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Mock Event
# Hardcoded some news for V0 to isolate and test the LLM's extraction logic.
daily_news = "United Airlines announces massive surge in bookings due to the upcoming World Cup, expecting record Q3 profits."

# Agentic Extraction via Ollama (local)
# This prompt strictly forces the LLM to output valid JSON and nothing else.
system_prompt = """
You are a financial AI. Read the news headline and output a raw JSON object with exactly three keys:
- "ticker": The stock ticker symbol of the company mentioned (e.g., "UAL").
- "action": "buy" if the news is positive, "sell" if negative.
- "reason": A one-sentence explanation.
Do NOT wrap the JSON in markdown code blocks. Do NOT output any conversational text. ONLY output the raw JSON.
"""

print("Agent is reading the news...")
response = ollama.chat(model='llama3.2:3b', messages=[
    {'role': 'system', 'content': system_prompt},
    {'role': 'user', 'content': daily_news}
])

llm_output = response['message']['content']

# Parse and Extracting
try:
    # Trying to parse the LLM's output into a Python dictionary
    decision = json.loads(llm_output)
    print("\n--- AI DECISION ---")
    print(f"Ticker: {decision.get('ticker')}")
    print(f"Action: {decision.get('action')}")
    print(f"Reason: {decision.get('reason')}\n")
    
except json.JSONDecodeError:
    print("\n[!] Error: The LLM hallucinated and did not return valid JSON.")
    print(f"Raw Output: {llm_output}")
    exit()

# If the AI decides to buy, execute a $5.00 fractional trade
if decision.get("action").lower() == "buy":
    target_ticker = decision.get("ticker").upper()
    print(f"Executing $5.00 buy order for {target_ticker}...")
    
    buy_order_data = MarketOrderRequest(
        symbol=target_ticker,
        notional=5.00, # Buying exactly $5 worth of shares
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    
    try:
        market_order = trading_client.submit_order(order_data=buy_order_data)
        print(f"Success! Order ID: {market_order.id}")
    except Exception as e:
        print(f"Alpaca API Error: {e}")
else:
    print("AI decided not to buy. No trade executed.")