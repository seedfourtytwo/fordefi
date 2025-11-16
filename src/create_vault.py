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
    Create a new vault via Fordefi API.
    
    Key concept: EVM vaults work across ALL EVM chains with a single address.
    The same vault address can be used on Ethereum, Unichain, Polygon, etc.
    Chain is specified per-transaction, not per-vault.
    
    Args:
        name: Human-readable name for the vault
        vault_type: Type of vault to create. Options:
                   - "evm" (default): EVM-compatible chains (Ethereum, Polygon, etc.)
                   - "bitcoin": Bitcoin vaults
                   - "solana": Solana vaults
                   - etc. (see Fordefi API docs for full list)
        
    Returns:
        dict: Vault object containing id, name, address, etc.
        
    Raises:
        requests.HTTPError: If API request fails
        
    Note:
        This assessment focuses on EVM vaults. Other vault types follow
        the same API pattern but may have different transaction structures.
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
