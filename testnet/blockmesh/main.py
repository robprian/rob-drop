import requests
import time
import os
import threading
from datetime import datetime
from colorama import init, Fore, Back, Style

init(autoreset=True)

def print_banner():
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}╔══════════════════════════════════════════════╗
║          BlockMesh Network AutoBot           ║
║     Github: https://github.com/robprian      ║
║      Welcome and do with your own risk!      ║
╚══════════════════════════════════════════════╝
"""
    print(banner)

# Global dictionaries to store tokens and proxy assignments
proxy_accounts = {}  # {proxy: {"email": email, "password": password, "token": token, "retries": 0}}
account_proxies = {}  # {email: proxy}
proxy_rotation_index = 0  # For rotating proxies when failures occur

print_banner()

# Read credentials from query.txt
credentials_list = []
query_file_path = "query.txt"

if os.path.exists(query_file_path):
    with open(query_file_path, "r") as file:
        credentials_list = [line.strip().split("|") for line in file if "|" in line]
        print(f"{Fore.GREEN}[✓] Loaded {len(credentials_list)} credentials from query.txt")
else:
    print(f"{Fore.RED}[×] query.txt not found!")
    exit()

if not credentials_list:
    print(f"{Fore.RED}[×] No valid credentials found in query.txt!")
    exit()

# Read proxies from proxies.txt
proxy_list_path = "proxies.txt"
proxies_list = []

if os.path.exists(proxy_list_path):
    with open(proxy_list_path, "r") as file:
        proxies_list = file.read().splitlines()
        print(f"{Fore.GREEN}[✓] Loaded {len(proxies_list)} proxies from proxies.txt")
else:
    print(f"{Fore.RED}[×] proxies.txt not found!")
    exit()

# Check if we have enough proxies for all accounts
if len(proxies_list) < len(credentials_list):
    print(f"{Fore.RED}[×] Not enough proxies for all accounts! Need at least {len(credentials_list)} proxies.")
    exit()

# Assign proxies to accounts with retry counter
for i, (email, password) in enumerate(credentials_list):
    proxy = proxies_list[i % len(proxies_list)]
    proxy_accounts[proxy] = {"email": email, "password": password, "token": None, "retries": 0}
    account_proxies[email] = proxy

# API endpoints
login_endpoint = "https://api.blockmesh.xyz/api/get_token"
report_endpoint = "https://app.blockmesh.xyz/api/report_uptime?email={email}&api_token={api_token}&ip={ip}"

# Headers
login_headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://app.blockmesh.xyz",
    "user-agent": "Mozilla/5.0 (WindowsNT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

report_headers = {
    "accept": "*/*",
    "content-type": "text/plain;charset=UTF-8",
    "user-agent": "Mozilla/5.0 (WindowsNT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def format_proxy(proxy_string):
    try:
        proxy_type, address = proxy_string.split("://")
        
        if "@" in address:
            credentials, host_port = address.split("@")
            username, password = credentials.split(":")
            host, port = host_port.split(":")
            proxy_dict = {
                "http": f"{proxy_type}://{username}:{password}@{host}:{port}",
                "https": f"{proxy_type}://{username}:{password}@{host}:{port}"
            }
        else:
            host, port = address.split(":")
            proxy_dict = {
                "http": f"{proxy_type}://{host}:{port}",
                "https": f"{proxy_type}://{host}:{port}"
            }
            
        return proxy_dict, host
    except Exception as e:
        print(f"{Fore.RED}Invalid proxy format: {proxy_string} - {str(e)}{Style.RESET_ALL}")
        return None, None

def get_next_proxy(current_proxy):
    global proxy_rotation_index
    if current_proxy in proxies_list:
        current_index = proxies_list.index(current_proxy)
    else:
        current_index = -1
    
    proxy_rotation_index = (proxy_rotation_index + 1) % len(proxies_list)
    return proxies_list[proxy_rotation_index]

def authenticate(proxy):
    proxy_config, ip_address = format_proxy(proxy)
    if proxy_config is None:
        return None, None, None
        
    account = proxy_accounts[proxy]
    email = account["email"]
    password = account["password"]
    
    if account["token"] is not None and account["retries"] < 3:
        return account["token"], ip_address, email
        
    login_data = {"email": email, "password": password}
    
    try:
        response = requests.post(login_endpoint, json=login_data, 
                               headers=login_headers, 
                               proxies=proxy_config,
                               timeout=30)
        response.raise_for_status()
        auth_data = response.json()
        api_token = auth_data.get("api_token")
        
        if not api_token:
            raise ValueError("No API token received")
            
        proxy_accounts[proxy]["token"] = api_token
        proxy_accounts[proxy]["retries"] = 0  # Reset retry counter on success
        
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.GREEN} Login successful {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_address}{Style.RESET_ALL}")
        return api_token, ip_address, email
    except Exception as err:
        proxy_accounts[proxy]["retries"] += 1
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.RED} Login failed (Attempt {proxy_accounts[proxy]['retries']}/3) {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_address}: {err}{Style.RESET_ALL}")
        
        if proxy_accounts[proxy]["retries"] >= 3:
            new_proxy = get_next_proxy(proxy)
            print(f"{Fore.YELLOW}Rotating proxy for {email} from {proxy} to {new_proxy}{Style.RESET_ALL}")
            # Migrate account to new proxy
            proxy_accounts[new_proxy] = proxy_accounts.pop(proxy)
            account_proxies[email] = new_proxy
            proxy_accounts[new_proxy]["retries"] = 0  # Reset retry counter
            
        return None, None, email

def send_uptime_report(api_token, ip_addr, email, proxy):
    proxy_config, _ = format_proxy(proxy)
    if proxy_config is None:
        return False
        
    formatted_url = report_endpoint.format(email=email, api_token=api_token, ip=ip_addr)
    
    try:
        response = requests.post(formatted_url, 
                               headers=report_headers, 
                               proxies=proxy_config,
                               timeout=30)
        response.raise_for_status()
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.LIGHTGREEN_EX} PING successful {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_addr}{Style.RESET_ALL}")
        return True
    except Exception as err:
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.RED} Failed to PING {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_addr}: {err}{Style.RESET_ALL}")
        return False

def process_proxy(proxy):
    while True:
        try:
            # Check if this proxy still has an account assigned
            if proxy not in proxy_accounts:
                break
                
            account = proxy_accounts[proxy]
            email = account["email"]
            
            # Authenticate (will handle proxy rotation if needed)
            api_token, ip_address, email = authenticate(proxy)
            
            if api_token:
                # Wait before first ping
                time.sleep(300)
                
                # Send uptime report
                success = send_uptime_report(api_token, ip_address, email, proxy)
                
                if not success:
                    # Reset token if ping failed
                    proxy_accounts[proxy]["token"] = None
                    
                # Wait between operations
                time.sleep(2)
            else:
                # Wait longer if auth failed
                time.sleep(10)
                
        except Exception as e:
            print(f"{Fore.RED}Unexpected error in thread for {proxy}: {str(e)}{Style.RESET_ALL}")
            time.sleep(30)  # Wait before retrying

def main():
    print(f"\n{Style.BRIGHT}Starting {len(credentials_list)} accounts with {len(proxies_list)} proxies...")
    threads = []
    
    # Create a thread for each proxy that has an account assigned
    for proxy in list(proxy_accounts.keys()):  # Use list() to avoid dict changed during iteration
        thread = threading.Thread(target=process_proxy, args=(proxy,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(1)  # Stagger thread starts
    
    print(f"{Fore.CYAN}[✓] All accounts started! Delay 5 minutes before first PING...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping all threads...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {str(e)}")
