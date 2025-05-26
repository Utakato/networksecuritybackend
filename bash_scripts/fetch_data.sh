solana gossip --output json > data/gossip_data.json
solana validators --output json > data/validators_data.json

python3 ../scripts/save_gossip.py