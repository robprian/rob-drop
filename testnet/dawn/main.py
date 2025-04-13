from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from colorama import *
from datetime import datetime
from fake_useragent import FakeUserAgent
import asyncio, json, os, pytz, uuid

wib = pytz.timezone('Asia/Jakarta')

class Dawn:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Host": "www.aeropres.in",
            "Origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": FakeUserAgent().random
        }
        self.extension_id = "fpdkjdnhkakefebpekbdhillbhonfjjp"
        self.proxies = []
        self.proxy_index = 0
        self.last_proxy_refresh = datetime.now()
        self.proxy_refresh_interval = 3600  # 1 hour in seconds

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, user, message):
        timestamp = f"{Fore.CYAN + Style.BRIGHT}[{datetime.now().astimezone(wib).strftime('%x %X %Z')}]{Style.RESET_ALL}"
        user_tag = f"{Fore.MAGENTA + Style.BRIGHT}[{user}]{Style.RESET_ALL}" if user else ""
        print(
            f"{timestamp}{user_tag} {message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.CYAN + Style.BRIGHT}╔══════════════════════════════════════════════════╗
        {Fore.CYAN + Style.BRIGHT}║{Fore.GREEN + Style.BRIGHT}           Auto Ping Dawn - BOT       {Fore.CYAN + Style.BRIGHT}║
        {Fore.CYAN + Style.BRIGHT}║{Fore.YELLOW + Style.BRIGHT}             Developed by: robprian                {Fore.CYAN + Style.BRIGHT}║
        {Fore.CYAN + Style.BRIGHT}║{Fore.WHITE + Style.BRIGHT}          https://github.com/robprian             {Fore.CYAN + Style.BRIGHT}║
        {Fore.CYAN + Style.BRIGHT}╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
            """
        )

    async def refresh_proxies_if_needed(self):
        now = datetime.now()
        if (now - self.last_proxy_refresh).total_seconds() >= self.proxy_refresh_interval:
            await self.load_auto_proxies()
            self.last_proxy_refresh = now

    async def load_auto_proxies(self):
        url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    
                    new_proxies = content.splitlines()
                    if not new_proxies:
                        self.log(None, f"{Fore.RED + Style.BRIGHT}No proxies found in the downloaded list!{Style.RESET_ALL}")
                        return
                    
                    self.proxies = new_proxies
                    self.proxy_index = 0  # Reset index when loading new proxies
                    self.log(None, f"{Fore.GREEN + Style.BRIGHT}Proxies successfully refreshed.{Style.RESET_ALL}")
                    self.log(None, f"{Fore.YELLOW + Style.BRIGHT}Loaded {len(self.proxies)} proxies.{Style.RESET_ALL}")
                    self.log(None, f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)
        except Exception as e:
            self.log(None, f"{Fore.RED + Style.BRIGHT}Failed to refresh proxies: {e}{Style.RESET_ALL}")
            return []
        
    async def load_manual_proxy(self):
        try:
            if not os.path.exists('proxy.txt'):
                self.log(None, f"{Fore.RED + Style.BRIGHT}Proxy file 'proxy.txt' not found!{Style.RESET_ALL}")
                return

            with open('proxy.txt', "r") as f:
                proxies = f.read().splitlines()

            self.proxies = proxies
            self.proxy_index = 0
            self.log(None, f"{Fore.YELLOW + Style.BRIGHT}Loaded {len(self.proxies)} proxies.{Style.RESET_ALL}")
            self.log(None, f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)
        except Exception as e:
            self.log(None, f"{Fore.RED + Style.BRIGHT}Failed to load manual proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy(self):
        if not self.proxies:
            self.log(None, f"{Fore.RED + Style.BRIGHT}No proxies available!{Style.RESET_ALL}")
            return None

        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.check_proxy_schemes(proxy)

    def load_accounts(self):
        try:
            if not os.path.exists('accounts.json'):
                self.log(None, f"{Fore.RED}File 'accounts.json' not found.{Style.RESET_ALL}")
                return []

            with open('accounts.json', 'r') as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
            
    def generate_app_id(self):
        prefix = "677eb"
        app_id = prefix + uuid.uuid4().hex[len(prefix):]
        return app_id
    
    def hide_email(self, email):
        local, domain = email.split('@', 1)
        hide_local = local[:3] + '*' * 3 + local[-3:]
        return f"{hide_local}@{domain}"
    
    def hide_token(self, token):
        hide_token = token[:3] + '*' * 3 + token[-3:]
        return hide_token
        
    async def user_data(self, app_id: str, email: str, token: str, proxy=None, retries=3):
        url = f"https://www.aeropres.in/api/atom/v1/userreferral/getpoint?appid={app_id}"
        headers = {
            **self.headers,
            "Authorization": f"Berear {token}",
            "Content-Type": "application/json",
        }
        
        for attempt in range(retries):
            try:
                connector = ProxyConnector.from_url(proxy) if proxy else None
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        if response.status == 400:
                            self.log(
                                self.hide_email(email),
                                f"{Fore.RED + Style.BRIGHT}Token Is Expired{Style.RESET_ALL}"
                            )
                            return None
                        
                        response.raise_for_status()
                        result = await response.json()
                        return result.get('data')
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
                self.log(
                    self.hide_email(email),
                    f"{Fore.RED + Style.BRIGHT}Failed to get user data: {str(e)}{Style.RESET_ALL}"
                )
                return None
        
    async def send_keepalive(self, app_id: str, email: str, token: str, proxy=None, retries=3):
        url = f"https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive?appid={app_id}"
        data = json.dumps({
            "username": email,
            "extensionid": self.extension_id,
            "numberoftabs": 0,
            "_v": "1.1.2"
        })
        headers = {
            **self.headers,
            "Authorization": f"Berear {token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
        }
        
        for attempt in range(retries):
            try:
                connector = ProxyConnector.from_url(proxy) if proxy else None
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
                self.log(
                    self.hide_email(email),
                    f"{Fore.RED + Style.BRIGHT}Failed to send keepalive: {str(e)}{Style.RESET_ALL}"
                )
                return None
            
    async def question(self):
        while True:
            try:
                print("1. Run With Auto Proxy")
                print("2. Run With Manual Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "With Auto Proxy" if choose == 1 else 
                        "With Manual Proxy" if choose == 2 else 
                        "Without Proxy"
                    )
                    self.log(None, f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Selected.{Style.RESET_ALL}")
                    await asyncio.sleep(1)
                    return choose
                else:
                    self.log(None, f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                self.log(None, f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")
        
    async def process_account(self, account, use_proxy):
        app_id = self.generate_app_id()
        email = account['Email']
        token = account['Token']
        hidden_email = self.hide_email(email)
        ping_count = 1
        proxy = None

        while True:
            if use_proxy:
                await self.refresh_proxies_if_needed()
                proxy = self.get_next_proxy()
                if not proxy:
                    await asyncio.sleep(60)
                    continue

            # Get user data
            user = await self.user_data(app_id, email, token, proxy)
            if not user:
                self.log(
                    hidden_email,
                    f"{Fore.RED + Style.BRIGHT}Login Failed{Style.RESET_ALL}"
                )
                await asyncio.sleep(10)
                continue

            # Display points information
            referral_point = user.get("referralPoint", {})
            reward_point = user.get("rewardPoint", {})
            commission_value = referral_point.get("commission", 0)
            total_reward_points = sum(
                value for key, value in reward_point.items()
                if "points" in key.lower() and isinstance(value, (int, float))
            )
            total_points = commission_value + total_reward_points
            
            self.log(
                hidden_email,
                f"{Fore.GREEN + Style.BRIGHT}Total Points: {total_points:.0f}{Style.RESET_ALL}"
            )

            # Send keepalive
            keepalive = await self.send_keepalive(app_id, email, token, proxy)
            if keepalive:
                self.log(
                    hidden_email,
                    f"{Fore.BLUE + Style.BRIGHT}Ping #{ping_count} Success{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | Proxy: {proxy if proxy else 'None'}{Style.RESET_ALL}"
                )
            else:
                self.log(
                    hidden_email,
                    f"{Fore.YELLOW + Style.BRIGHT}Ping #{ping_count} Failed{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | Proxy: {proxy if proxy else 'None'}{Style.RESET_ALL}"
                )

            ping_count += 1
            await asyncio.sleep(180)  # Wait 3 minutes between pings
    
    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                self.log(None, f"{Fore.RED}No accounts loaded from 'accounts.json'.{Style.RESET_ALL}")
                return
            
            use_proxy_choice = await self.question()
            use_proxy = use_proxy_choice in [1, 2]

            self.clear_terminal()
            self.welcome()
            self.log(None, f"{Fore.GREEN + Style.BRIGHT}Total Accounts: {len(accounts)}{Style.RESET_ALL}")
            self.log(None, f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

            if use_proxy:
                if use_proxy_choice == 1:
                    await self.load_auto_proxies()
                else:
                    await self.load_manual_proxy()

            # Create tasks for all accounts
            tasks = [self.process_account(account, use_proxy) for account in accounts]
            await asyncio.gather(*tasks)

        except Exception as e:
            self.log(None, f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
        except KeyboardInterrupt:
            self.log(None, f"{Fore.RED + Style.BRIGHT}Bot stopped by user.{Style.RESET_ALL}")

if __name__ == "__main__":
    bot = Dawn()
    try:
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print("\n")
        bot.log(None, f"{Fore.RED + Style.BRIGHT}Bot stopped by user.{Style.RESET_ALL}")