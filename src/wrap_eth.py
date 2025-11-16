#!/usr/bin/env python3
"""
Wrap ETH into WETH via Fordefi API.
Creates and signs a contract call transaction to WETH deposit() function.

Current: Requires command-line arguments
Future: Could add interactive prompts for vault selection and amount
"""

import requests
import json
import time
import base64
from config import Config
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


def sign_request(path, body, timestamp, private_key):
    """
    Sign API request using ECDSA P-256 signature.
    
    Fordefi requires all transaction requests to be signed.
    Message format: path|timestamp|body (concatenated with pipe separators)
    
    IMPORTANT: ec.ECDSA(hashes.SHA256()) performs SHA256 hashing internally.
    Do NOT pre-hash the message - pass raw message string.
    
    Args:
        path: API endpoint path (e.g., "/api/v1/transactions")
        body: JSON request body as string
        timestamp: Unix timestamp in milliseconds (as string)
        private_key: ECDSA P-256 private key object
        
    Returns:
        str: Base64-encoded DER signature
    """
    # Construct message: path|timestamp|body
    message = f"{path}|{timestamp}|{body}"
    
    # Sign with ECDSA P-256 (SHA256 hashing done internally)
    signature = private_key.sign(message.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    
    # Return base64-encoded signature for HTTP header
    return base64.b64encode(signature).decode('utf-8')


def wrap_eth(vault_id, amount_wei, weth_address, chain_id="11155111"):
    """
    Wrap ETH to WETH by calling WETH deposit() function.
    
    Uses evm_raw_transaction type to make a smart contract call.
    WETH wrapping: send ETH with value, call deposit() function.
    
    Args:
        vault_id: UUID of the vault to wrap ETH from
        amount_wei: Amount of ETH to wrap (in wei, 10^18 wei = 1 ETH)
        weth_address: WETH contract address
        chain_id: EVM chain ID (default: "11155111" for Sepolia)
        
    Returns:
        dict: Transaction object with id, hash, explorer_url, etc.
        
    Raises:
        requests.HTTPError: If API request fails
    """
    Config.validate()
    
    # ========================================================================
    # Load ECDSA P-256 private key for request signing
    # ========================================================================
    with open(Config.PRIVATE_KEY_PATH, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    
    # ========================================================================
    # Prepare contract call data
    # ========================================================================
    # WETH deposit() function selector: first 4 bytes of keccak256("deposit()")
    # No parameters needed - amount specified in transaction value
    function_selector = "0xd0e30db0"
    
    # ========================================================================
    # Build raw transaction for contract call
    # ========================================================================
    # Uses evm_raw_transaction type for direct smart contract interaction
    body = {
        "vault_id": vault_id,
        "signer_type": "api_signer",
        "type": "evm_transaction",
        "details": {
            "type": "evm_raw_transaction",        # Raw transaction for contract calls
            "to": weth_address,                    # WETH contract address
            "value": str(amount_wei),              # ETH amount (as string, not object)
            "data": {                              # Contract function call data
                "type": "hex",                     # Data type discriminator
                "hex_data": function_selector      # deposit() function selector
            },
            "chain": f"evm_{chain_id}"            # Chain identifier format: evm_<chain_id>
        },
        "note": "Wrap ETH to WETH via API"
    }
    
    # ========================================================================
    # Sign request with ECDSA P-256 signature
    # ========================================================================
    path = "/api/v1/transactions"
    timestamp = str(int(time.time() * 1000))  # Current time in milliseconds
    body_json = json.dumps(body, separators=(',', ':'))  # Compact JSON (no spaces)
    signature = sign_request(path, body_json, timestamp, private_key)
    
    # ========================================================================
    # Submit signed transaction to Fordefi API
    # ========================================================================
    headers = {
        "Authorization": f"Bearer {Config.ACCESS_TOKEN}",  # API access token
        "Content-Type": "application/json",
        "x-signature": signature,    # ECDSA P-256 signature
        "x-timestamp": timestamp      # Request timestamp
    }
    
    response = requests.post(f"{Config.API_URL}{path}", headers=headers, data=body_json, timeout=30)
    
    # Handle errors with detailed error message
    if response.status_code >= 400:
        print(f"Error {response.status_code}: {response.text}")
        response.raise_for_status()
    
    return response.json()


# ============================================================================
# Command-line interface
# ============================================================================
if __name__ == "__main__":
    import sys
    
    # Validate command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python3 wrap_eth.py <vault_id> <amount_wei> [weth_address] [chain_id]")
        print("\nExample (Sepolia):")
        print("  python3 wrap_eth.py \\")
        print("    646c57e4-bbb4-434f-855f-e0141a88265d \\")
        print("    100000000000000000 \\")
        print("    0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14 \\")
        print("    11155111")
        print("\nNote: amount_wei is in wei (1 ETH = 1000000000000000000 wei)")
        sys.exit(1)
    
    # Parse command-line arguments with defaults from Config
    vault_id = sys.argv[1]
    amount_wei = int(sys.argv[2])
    weth_address = sys.argv[3] if len(sys.argv) > 3 else Config.SEPOLIA_WETH_ADDRESS
    chain_id = sys.argv[4] if len(sys.argv) > 4 else Config.SEPOLIA_CHAIN_ID
    
    # Display operation details
    print(f"Wrapping {amount_wei} wei ({amount_wei / 1e18:.6f} ETH) to WETH")
    print(f"WETH Contract: {weth_address}")
    print(f"Chain ID: {chain_id}")
    
    # Execute wrap
    transaction = wrap_eth(vault_id, amount_wei, weth_address, chain_id)
    
    # Display results
    print(f"✅ Transaction: {transaction['id']}")
    print(f"   Hash: {transaction.get('hash', 'pending')}")
    print(f"   Explorer: {transaction.get('explorer_url', 'N/A')}")

