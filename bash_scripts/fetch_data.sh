solana gossip --output json > gossip_service/gossip_data.json && python3 ./gossip_service/main.py
solana validators --output json > data/validators_data.json && python3 ./validators_service/main.py