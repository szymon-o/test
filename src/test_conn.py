import os
from dotenv import load_dotenv
from opinion_clob_sdk import Client

# Load environment variables
load_dotenv()

# Initialize client
client = Client(
    host='https://proxy.opinion.trade:8443',
    apikey=os.getenv('OPINION_API_KEY'),
    chain_id=56,  # BNB Chain mainnet
    rpc_url=os.getenv('RPC_URL'),
    private_key=os.getenv('PRIVATE_KEY'),
    multi_sig_addr=os.getenv('MULTI_SIG_ADDRESS'),
    # conditional_tokens_addr=os.getenv('CONDITIONAL_TOKEN_ADDR'),
    # multisend_addr=os.getenv('0x998739BFdAAdde7C933B942a68053933098f9EDa')
)

print("✓ Client initialized successfully!")

token_id = "5594416680819798108754390494196008171649235279665203626651921875543745446256"  # Replace with actual token ID

try:
    orderbook = client.get_orderbook(token_id)
    if orderbook.errno == 0:
        print(orderbook.result.asks)
        # [OpenapiOrderbookLevel(price='0.187000000000000000', size='36.85'), OpenapiOrderbookLevel(price='0.202000000000000000', size='12.53'), OpenapiOrderbookLevel(price='0.239000000000000000', size='1.52'), OpenapiOrderbookLevel(price='0.416000000000000000', size='3841.890985576923'), OpenapiOrderbookLevel(price='0.995000000000000000', size='1.5'), OpenapiOrderbookLevel(price='0.998000000000000000', size='1000'), OpenapiOrderbookLevel(price='0.153000000000000000', size='168.83'), OpenapiOrderbookLevel(price='0.180000000000000000', size='1699.083388888889'), OpenapiOrderbookLevel(price='0.495000000000000000', size='170.15'), OpenapiOrderbookLevel(price='0.999000000000000000', size='10267.93'), OpenapiOrderbookLevel(price='0.137000000000000000', size='11.11'), OpenapiOrderbookLevel(price='0.422000000000000000', size='0.39'), OpenapiOrderbookLevel(price='0.415000000000000000', size='500'), OpenapiOrderbookLevel(price='0.450000000000000000', size='400'), OpenapiOrderbookLevel(price='0.515000000000000000', size='37.11000000000001'), OpenapiOrderbookLevel(price='0.915000000000000000', size='1.6'), OpenapiOrderbookLevel(price='0.980000000000000000', size='5000.2'), OpenapiOrderbookLevel(price='0.104000000000000000', size='16.00653846153847'), OpenapiOrderbookLevel(price='0.245000000000000000', size='1000'), OpenapiOrderbookLevel(price='0.244000000000000000', size='40.76'), OpenapiOrderbookLevel(price='0.275000000000000000', size='10.48'), OpenapiOrderbookLevel(price='0.984000000000000000', size='3750'), OpenapiOrderbookLevel(price='0.126000000000000000', size='153.98'), OpenapiOrderbookLevel(price='0.133000000000000000', size='977.1689351787774')]
        print(orderbook.result.bids)
        # [OpenapiOrderbookLevel(price='0.001000000000000000', size='10050'), OpenapiOrderbookLevel(price='0.078000000000000000', size='223.49'), OpenapiOrderbookLevel(price='0.077000000000000000', size='424.67'), OpenapiOrderbookLevel(price='0.060000000000000000', size='833.33'), OpenapiOrderbookLevel(price='0.010000000000000000', size='3000')]
except Exception as e:
    print(f"  (Skip if token_id not set: {e})")