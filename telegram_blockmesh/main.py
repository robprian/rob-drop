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
proxy_accounts = {}  # {proxy: {"email": email, "password": password, "token": token}}
account_proxies = {}  # {email: proxy}

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

# Assign proxies to accounts
for i, (email, password) in enumerate(credentials_list):
    proxy = proxies_list[i % len(proxies_list)]  # Round-robin assignment
    proxy_accounts[proxy] = {"email": email, "password": password, "token": None}
    account_proxies[email] = proxy

# API endpoints
login_endpoint = "https://api.blockmesh.xyz/api/get_token"
report_endpoint = "https://app.blockmesh.xyz/api/report_uptime?email={email}&api_token={api_token}&ip={ip}"

# Headers
login_headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://app.blockmesh.xyz",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

report_headers = {
    "accept": "*/*",
    "content-type": "text/plain;charset=UTF-8",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def format_proxy(proxy_string):
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

def authenticate(proxy):
    proxy_config, ip_address = format_proxy(proxy)
    account = proxy_accounts[proxy]
    email = account["email"]
    password = account["password"]
    
    if account["token"] is not None:
        return account["token"], ip_address, email
        
    login_data = {"email": email, "password": password}
    
    try:
        response = requests.post(login_endpoint, json=login_data, headers=login_headers, proxies=proxy_config)
        response.raise_for_status()
        auth_data = response.json()
        api_token = auth_data.get("api_token")
        
        proxy_accounts[proxy]["token"] = api_token
        
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.GREEN} Login successfully {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_address}{Style.RESET_ALL}")
        return api_token, ip_address, email
    except requests.RequestException as err:
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.RED} Login failed {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_address}: {err}{Style.RESET_ALL}")
        return None, None, email

def send_uptime_report(api_token, ip_addr, email, proxy):
    proxy_config, _ = format_proxy(proxy)
    formatted_url = report_endpoint.format(email=email, api_token=api_token, ip=ip_addr)
    
    try:
        response = requests.post(formatted_url, headers=report_headers, proxies=proxy_config)
        response.raise_for_status()
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.LIGHTGREEN_EX} PING successfully {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_addr}{Style.RESET_ALL}")
    except requests.RequestException as err:
        proxy_accounts[proxy]["token"] = None  # Reset token on failure
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}][{email}]{Fore.RED} Failed to PING {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_addr}: {err}{Style.RESET_ALL}")

def process_proxy(proxy):
    first_run = True
    while True:
        if first_run or proxy_accounts[proxy]["token"] is None:
            api_token, ip_address, email = authenticate(proxy)
            first_run = False
        else:
            api_token = proxy_accounts[proxy]["token"]
            _, ip_address = format_proxy(proxy)
            email = proxy_accounts[proxy]["email"]
            
        if api_token:
            time.sleep(300)  # 5 minute delay between reports
            send_uptime_report(api_token, ip_address, email, proxy)
        time.sleep(2)

def main():
    print(f"\n{Style.BRIGHT}Starting {len(credentials_list)} accounts with {len(proxies_list)} proxies...")
    threads = []
    
    # Create a thread for each proxy that has an account assigned
    for proxy in proxy_accounts:
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
