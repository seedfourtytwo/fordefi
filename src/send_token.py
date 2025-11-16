#!/usr/bin/env python3
"""
Send ERC20 tokens via Fordefi API.
Creates and signs a token transfer transaction.

Current: Requires command-line arguments
Future: Could add interactive prompts for vault selection, token, amount
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


def send_token(vault_id, recipient_address, amount_wei, token_address, chain_id="130"):
    """
    Send ERC20 tokens using evm_transfer transaction type.
    
    This function builds and submits an ERC20 token transfer transaction.
    Uses evm_transfer type which handles ERC20-specific transaction construction.
    
    Args:
        vault_id: UUID of the vault to send from
        recipient_address: Ethereum address to send tokens to
        amount_wei: Amount in token's smallest unit (e.g., wei for ETH, 10^6 for USDC)
        token_address: Contract address of the ERC20 token
        chain_id: EVM chain ID (default: "130" for Unichain)
        
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
    # Build ERC20 transfer transaction body
    # ========================================================================
    # Uses evm_transfer type with asset_identifier for ERC20 tokens
    # Key differences from evm_raw_transaction (see wrap_eth.py):
    #   - value: object with type/value fields (not plain string)
    #   - asset_identifier: specifies token details (not used in raw transactions)
    #   - chain_id: separate field (vs "chain" string in raw transactions)
    body = {
        "vault_id": vault_id,
        "signer_type": "api_signer",
        "type": "evm_transaction",
        "details": {
            "type": "evm_transfer",              # High-level transfer type for tokens
            "to": recipient_address,
            "value": {"type": "value", "value": str(amount_wei)},  # Object format
            "asset_identifier": {                # Specifies which token to transfer
                "type": "evm",
                "details": {
                    "type": "erc20",             # ERC20 token type
                    "token": {
                        "chain": f"evm_{chain_id}",    # Chain identifier
                        "chain_id": chain_id,           # Numeric chain ID
                        "hex_repr": token_address       # Token contract address
                    }
                }
            }
        },
        "note": "Token transfer via API"
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
    if len(sys.argv) < 5:
        print("Usage: python3 send_token.py <vault_id> <recipient> <amount> <token_address> [chain_id]")
        print("\nExample (Task 1):")
        print("  python3 send_token.py \\")
        print("    17332797-9d4e-4a97-8977-502863b7bc8c \\")
        print("    0x8BFCF9e2764BC84DE4BBd0a0f5AAF19F47027A73 \\")
        print("    1000000 \\")
        print("    0x078D782b760474a361dDA0AF3839290b0EF57AD6 \\")
        print("    130")
        sys.exit(1)
    
    # Parse command-line arguments
    vault_id = sys.argv[1]
    recipient = sys.argv[2]
    amount = int(sys.argv[3])
    token_address = sys.argv[4]
    chain_id = sys.argv[5] if len(sys.argv) > 5 else "130"  # Default to Unichain
    
    # Execute transfer
    print(f"Sending {amount} tokens to {recipient}")
    transaction = send_token(vault_id, recipient, amount, token_address, chain_id)
    
    # Display results
    print(f"✅ Transaction: {transaction['id']}")
    print(f"   Hash: {transaction.get('hash', 'pending')}")
    print(f"   Explorer: {transaction.get('explorer_url', 'N/A')}")
