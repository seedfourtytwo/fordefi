#!/usr/bin/env python3
"""
Create vaults via Fordefi API.

Current: Interactive input fallback if no args provided
Future: Could add vault type selection, chain preference configuration
"""

import sys
import requests
from config import Config


def create_vault(name, vault_type="evm"):
    """
    Create a new EVM vault via Fordefi API.
    
    Key concept: EVM vaults work across ALL EVM chains with a single address.
    The same vault address can be used on Ethereum, Unichain, Polygon, etc.
    Chain is specified per-transaction, not per-vault.
    
    Args:
        name: Human-readable name for the vault
        vault_type: Type of vault (default: "evm" for EVM-compatible chains)
        
    Returns:
        dict: Vault object containing id, name, address, etc.
        
    Raises:
        requests.HTTPError: If API request fails
    """
    # Validate configuration before making API calls
    Config.validate()
    
    # Make API request to create vault
    response = requests.post(
        f"{Config.API_URL}/api/v1/vaults",
        headers={
            "Authorization": f"Bearer {Config.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json={"name": name, "type": vault_type},
        timeout=30
    )
    response.raise_for_status()
    
    # Parse response and display vault details
    vault = response.json()
    print(f"✅ Vault created: {vault['name']}")
    print(f"   ID: {vault['id']}")
    print(f"   Address: {vault.get('address', 'N/A')}")
    return vault


if __name__ == "__main__":
    # Accept vault name from command line or prompt user
    vault_name = sys.argv[1] if len(sys.argv) > 1 else input("Vault name: ")
    create_vault(vault_name)
