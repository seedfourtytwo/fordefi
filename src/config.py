#!/usr/bin/env python3
"""Configuration management for Fordefi API integration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Centralized configuration for Fordefi API operations.
    
    All sensitive data (tokens, keys) loaded from environment variables.
    Network-specific constants defined here for easy reference across scripts.
    """
    
    # ============================================================================
    # API Configuration
    # ============================================================================
    API_URL = "https://api.fordefi.com"
    ACCESS_TOKEN = os.getenv("FORDEFI_ACCESS_TOKEN")  # From Fordefi console
    ORG_ID = os.getenv("FORDEFI_ORG_ID")              # From Fordefi console
    PRIVATE_KEY_PATH = os.getenv("FORDEFI_PRIVATE_KEY_PATH", "./private.pem")
    
    # ============================================================================
    # Network Configuration - Unichain Sepolia (Task 1)
    # ============================================================================
    UNICHAIN_CHAIN_ID = "130"
    UNICHAIN_USDC_ADDRESS = "0x078D782b760474a361dDA0AF3839290b0EF57AD6"
    UNICHAIN_VAULT_ID = os.getenv("UNICHAIN_VAULT_ID", "")
    
    # ============================================================================
    # Network Configuration - Ethereum Sepolia (Task 2)
    # ============================================================================
    SEPOLIA_CHAIN_ID = "11155111"
    SEPOLIA_WETH_ADDRESS = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"
    SEPOLIA_VAULT_ID = os.getenv("SEPOLIA_VAULT_ID", "")
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration is present.
        
        Checks:
        - ACCESS_TOKEN exists in environment
        - ORG_ID exists in environment
        - Private key file exists at specified path
        
        Raises:
            ValueError: If required environment variables are missing
            FileNotFoundError: If private key file doesn't exist
            
        Returns:
            bool: True if all validation passes
        """
        if not cls.ACCESS_TOKEN:
            raise ValueError("FORDEFI_ACCESS_TOKEN not set in environment")
        if not cls.ORG_ID:
            raise ValueError("FORDEFI_ORG_ID not set in environment")
        if not Path(cls.PRIVATE_KEY_PATH).exists():
            raise FileNotFoundError(f"Private key not found: {cls.PRIVATE_KEY_PATH}")
        return True
