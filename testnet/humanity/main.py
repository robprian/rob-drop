from web3 import Web3
from colorama import init, Fore, Style
import sys
import time
import os
import requests
import json
from config import rpc_url, contract_address, contract_abi, faucet_url
import random
from itertools import cycle
from datetime import datetime, timedelta

# Initialize colorama
init(autoreset=True)

def display_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_text = f"""
{Fore.CYAN}{Style.BRIGHT}
    ╔═══════════════════════════════════════════╗
    ║        🚀 Humanity Protocol Bot          ║
    ║  ------------------------------------    ║
    ║    💰 Auto Claim RWT & THP Rewards      ║
    ║    🔥 Created by: rbbaprianto           ║
    ║    🌐 Version: 1.0.1                    ║
    ║    ⏱ Current Time: {current_time}       ║
    ╚═══════════════════════════════════════════╝
    """
    print(header_text)

def setup_blockchain_connection(rpc_url):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if web3.is_connected():
        print(f"{Fore.GREEN}✓ Connected to Humanity Protocol")
        print(f"{Fore.BLUE}ℹ Chain ID: {web3.eth.chain_id}")
        print(f"{Fore.BLUE}ℹ Latest Block: {web3.eth.block_number}")
    else:
        print(f"{Fore.RED}✖ Connection failed. Exiting...")
        sys.exit(1)
    return web3

def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}✖ Error: query.txt not found!")
        sys.exit(1)

def loading_animation(message, duration=3):
    animation = ["◐", "◓", "◑", "◒"]
    for i in range(duration * 4):
        sys.stdout.write(f"\r{Fore.YELLOW}{message} {animation[i % len(animation)]}")
        sys.stdout.flush()
        time.sleep(0.25)
    sys.stdout.write("\r")

def load_claim_history():
    try:
        with open('claim_history.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_claim_history(history):
    with open('claim_history.json', 'w') as f:
        json.dump(history, f, indent=4)

def format_time_remaining(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

def claim_thp_from_faucet(private_key, web3, retries=3):
    try:
        account = web3.eth.account.from_key(private_key)
        sender_address = account.address
        
        claim_history = load_claim_history()
        wallet_history = claim_history.get(sender_address, {})
        last_thp_claim = wallet_history.get('last_thp_claim')
        
        current_time = datetime.now()
        
        if last_thp_claim:
            last_claim_time = datetime.fromisoformat(last_thp_claim)
            time_since_claim = current_time - last_claim_time
            
            if time_since_claim < timedelta(hours=24):
                remaining_time = timedelta(hours=24) - time_since_claim
                print(f"{Fore.YELLOW}⏳ THP Faucet: Wait time remaining for {sender_address}: {format_time_remaining(remaining_time.total_seconds())}")
                next_claim_time = last_claim_time + timedelta(hours=24)
                print(f"{Fore.YELLOW}📅 Next claim available at: {next_claim_time.strftime('%Y-%m-%d %H:%M:%S')}")
                return False

        print(f"{Fore.BLUE}🚰 Requesting THP from faucet for {sender_address}...")
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://faucet.testnet.humanity.org',
            'Referer': 'https://faucet.testnet.humanity.org/'
        }
        
        data = {
            'address': sender_address
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(
                    faucet_url,
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        wallet_history['last_thp_claim'] = current_time.isoformat()
                        claim_history[sender_address] = wallet_history
                        save_claim_history(claim_history)
                        
                        if 'txHash' in result:
                            print(f"{Fore.GREEN}✓ THP Faucet Success: {sender_address} - TX Hash: {result['txHash']}")
                        else:
                            print(f"{Fore.GREEN}✓ THP Faucet Request Successful for {sender_address}")
                        return True
                    except json.JSONDecodeError:
                        print(f"{Fore.RED}✖ Invalid JSON response from faucet for {sender_address}")
                
                elif response.status_code == 429:
                    print(f"{Fore.YELLOW}⚠ THP Faucet: Rate limit reached for {sender_address}")
                    time.sleep((attempt + 1) * 10)  # Exponential backoff
                    continue
                
                elif response.status_code == 400:
                    error_data = response.json() if response.text else {'message': 'Unknown error'}
                    if 'message' in error_data and 'too soon' in error_data['message'].lower():
                        print(f"{Fore.YELLOW}⚠ THP Faucet: Too soon to request again for {sender_address}")
                        return False
                    else:
                        print(f"{Fore.RED}✖ THP Faucet Error: {error_data.get('message', 'Unknown error')}")
                
                else:
                    print(f"{Fore.RED}✖ THP Faucet Request failed with status {response.status_code}")
                    print(f"{Fore.RED}Response: {response.text}")
            
            except requests.exceptions.RequestException as req_err:
                print(f"{Fore.RED}✖ Attempt {attempt + 1}/{retries} failed: {str(req_err)}")
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 5)  # Exponential backoff
                continue
        
        return False
    
    except Exception as e:
        print(f"{Fore.RED}✖ Error requesting THP from faucet for {sender_address}: {str(e)}")
        return False

def process_claim(sender_address, private_key, web3, contract):
    try:
        loading_animation(f"⚙ Processing claim for {sender_address}")
        
        # Estimate gas
        gas_estimate = contract.functions.claimReward().estimate_gas({
            'from': sender_address,
            'nonce': web3.eth.get_transaction_count(sender_address)
        })
        
        # Build transaction with 20% gas buffer
        transaction = contract.functions.claimReward().build_transaction({
            'chainId': web3.eth.chain_id,
            'gas': int(gas_estimate * 1.2),
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(sender_address)
        })
        
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if tx_receipt.status == 1:
            print(f"{Fore.GREEN}✓ Success: {sender_address} - TX Hash: {web3.to_hex(tx_hash)}")
            return True
        else:
            print(f"{Fore.RED}✖ Transaction failed for {sender_address}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}✖ Error processing claim for {sender_address}: {str(e)}")
        return False

def claim_rewards(private_key, web3, contract):
    try:
        account = web3.eth.account.from_key(private_key)
        sender_address = account.address
        
        claim_history = load_claim_history()
        wallet_history = claim_history.get(sender_address, {})
        current_time = datetime.now()
        
        current_epoch = contract.functions.currentEpoch().call()
        genesis_claimed = contract.functions.userGenesisClaimStatus(sender_address).call()
        buffer_amount, claim_status = contract.functions.userClaimStatus(sender_address, current_epoch).call()

        if not claim_status:
            claim_type = "Genesis" if not genesis_claimed else "Regular"
            print(f"{Fore.GREEN}🚀 Claiming {claim_type} reward for {sender_address}...")
            
            success = process_claim(sender_address, private_key, web3, contract)
            
            if success:
                wallet_history['last_rwt_claim'] = current_time.isoformat()
                wallet_history['last_epoch'] = current_epoch
                claim_history[sender_address] = wallet_history
                save_claim_history(claim_history)
                return True
            return False
        else:
            last_claim = wallet_history.get('last_rwt_claim', 'Never')
            print(f"{Fore.YELLOW}⚠ Reward already claimed for {sender_address}")
            print(f"{Fore.YELLOW}📅 Last claim: {last_claim}")
            print(f"{Fore.YELLOW}🔄 Current Epoch: {current_epoch}")
            return False

    except Exception as e:
        print(f"{Fore.RED}✖ Error in claim_rewards for {sender_address}: {str(e)}")
        return False

def display_summary():
    claim_history = load_claim_history()
    current_time = datetime.now()
    
    print("\n" + Fore.CYAN + "═" * 70)
    print(f"{Fore.BLUE}{Style.BRIGHT} 📊 Claim Status Summary")
    print(Fore.CYAN + "═" * 70)
    
    for address, history in claim_history.items():
        print(f"\n{Fore.WHITE}🔍 Wallet: {address}")
        
        if 'last_thp_claim' in history:
            last_thp = datetime.fromisoformat(history['last_thp_claim'])
            time_since_thp = current_time - last_thp
            next_thp = last_thp + timedelta(hours=24)
            if time_since_thp < timedelta(hours=24):
                remaining = timedelta(hours=24) - time_since_thp
                print(f"{Fore.YELLOW}🚰 THP Next Claim: {format_time_remaining(remaining.total_seconds())} remaining")
            else:
                print(f"{Fore.GREEN}🚰 THP Ready to Claim!")
        
        if 'last_rwt_claim' in history:
            print(f"{Fore.BLUE}💰 RWT Last Claim: {history['last_rwt_claim']}")
            print(f"{Fore.BLUE}🔄 Last Epoch: {history.get('last_epoch', 'Unknown')}")
    
    print(Fore.CYAN + "═" * 70 + "\n")

def main_loop():
    display_header()
    private_keys = load_private_keys('query.txt')
    
    web3 = setup_blockchain_connection(rpc_url)
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=contract_abi
    )
    
    last_rwt_claim_time = None
    
    while True:
        current_time = datetime.now()
        
        # THP Claims (every 60 seconds per wallet)
        for private_key in private_keys:
            claim_thp_from_faucet(private_key, web3)
            time.sleep(60)
        
        # RWT Claims (every 24 hours)
        if not last_rwt_claim_time or (current_time - last_rwt_claim_time) >= timedelta(hours=24):
            print(f"\n{Fore.CYAN}🚀 Starting RWT Reward Claims...")
            
            for private_key in private_keys:
                claim_rewards(private_key, web3, contract)
                time.sleep(5)  # Small delay between wallet claims
            
            last_rwt_claim_time = current_time
            display_summary()
        
        # Calculate next claim time
        if last_rwt_claim_time:
            next_rwt_claim = last_rwt_claim_time + timedelta(hours=24)
            time_until_next = next_rwt_claim - current_time
            print(f"{Fore.CYAN}⏳ Next RWT claim in: {format_time_remaining(time_until_next.total_seconds())}")
            print(f"{Fore.CYAN}📅 Next RWT claim at: {next_rwt_claim.strftime('%Y-%m-%d %H:%M:%S')}")
        
        time.sleep(30)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Script stopped by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}‼ Unhandled error: {str(e)}")
        sys.exit(1)