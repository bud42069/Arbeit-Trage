#!/usr/bin/env python3
"""Test script to debug Whirlpool account parsing."""
import asyncio
from decimal import Decimal
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey


async def main():
    # Connect to Helius
    helius_url = "https://mainnet.helius-rpc.com/?api-key=625e29ab-4bea-4694-b7d8-9fdda5871969"
    client = AsyncClient(helius_url)
    
    # Orca Whirlpool SOL/USDC pool
    pool_address = "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"
    pubkey = Pubkey.from_string(pool_address)
    
    print(f"Fetching account: {pool_address}")
    response = await client.get_account_info(pubkey)
    
    if not response.value or not response.value.data:
        print("No account data!")
        return
    
    account_data = bytes(response.value.data)
    print(f"\nAccount data length: {len(account_data)} bytes")
    print(f"First 16 bytes (hex):  {account_data[:16].hex()}")
    print(f"Bytes 65-81 (hex):     {account_data[65:81].hex()}")
    print(f"Bytes 128-144 (hex):   {account_data[128:144].hex()}")
    
    # Try offset 65
    print("\n--- Testing Offset 65 ---")
    sqrt_price_bytes_65 = account_data[65:81]
    sqrt_price_raw_65 = int.from_bytes(sqrt_price_bytes_65, byteorder='little')
    sqrt_price_decimal_65 = Decimal(sqrt_price_raw_65) / Decimal(2 ** 64)
    price_65 = sqrt_price_decimal_65 ** 2
    print(f"Raw: {sqrt_price_raw_65}")
    print(f"Sqrt: {sqrt_price_decimal_65}")
    print(f"Price (before decimals): {price_65}")
    price_65_adjusted = price_65 * Decimal(10) ** (6 - 9)
    print(f"Price (with 6-9 decimals): {price_65_adjusted}")
    price_65_adjusted_inv = price_65 * Decimal(10) ** (9 - 6)
    print(f"Price (with 9-6 decimals): {price_65_adjusted_inv}")
    
    # Try offset 128
    print("\n--- Testing Offset 128 ---")
    sqrt_price_bytes_128 = account_data[128:144]
    sqrt_price_raw_128 = int.from_bytes(sqrt_price_bytes_128, byteorder='little')
    sqrt_price_decimal_128 = Decimal(sqrt_price_raw_128) / Decimal(2 ** 64)
    price_128 = sqrt_price_decimal_128 ** 2
    print(f"Raw: {sqrt_price_raw_128}")
    print(f"Sqrt: {sqrt_price_decimal_128}")
    print(f"Price (before decimals): {price_128}")
    price_128_adjusted = price_128 * Decimal(10) ** (6 - 9)
    print(f"Price (with 6-9 decimals): {price_128_adjusted}")
    price_128_adjusted_inv = price_128 * Decimal(10) ** (9 - 6)
    print(f"Price (with 9-6 decimals): {price_128_adjusted_inv}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
