import asyncio
import aiohttp
import aiohttp_socks
import time
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from typing import List, Dict
from urllib.parse import urlparse
import json
from rich.progress import Progress

console = Console()

class ProxyChecker:
    def __init__(self, proxy_file: str, timeout: int = 10, max_concurrent: int = 50, 
                 retries: int = 2, test_url: str = "http://ip-api.com/json"):
        self.proxy_file = proxy_file
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.retries = retries
        self.test_url = test_url
        self.results: List[Dict] = []
        self.working_proxies: List[str] = []
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.failed_proxies: List[str] = []

    async def check_proxy(self, proxy: str):
        async with self.semaphore:  # Move semaphore here for better control
            for attempt in range(self.retries + 1):
                try:
                    return await self._check_proxy_impl(proxy)
                except Exception as e:
                    if attempt == self.retries:
                        return self._create_error_result(proxy, str(e))
                    await asyncio.sleep(1)

    async def _check_proxy_impl(self, proxy: str):
        original_proxy = proxy
        try:
            # Auto-detect protocol if missing
            if not proxy.startswith(('http://', 'socks5://')):
                proxy = self._detect_protocol(proxy)

            start_time = time.time()
            
            # Parse proxy URL
            parsed = urlparse(proxy)
            proxy_type = parsed.scheme
            auth = None
            if parsed.username and parsed.password:
                auth = aiohttp.BasicAuth(parsed.username, parsed.password)

            # Create connector based on proxy type
            if proxy_type == 'socks5':
                connector = aiohttp_socks.ProxyConnector.from_url(proxy)
            else:
                connector = aiohttp.TCPConnector()

            # Modify the session creation to include random user-agent
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            async with aiohttp.ClientSession(connector=connector, auth=auth, headers=headers) as session:
                if proxy_type == 'http':
                    proxy_url = f"http://{parsed.hostname}:{parsed.port}"
                    async with session.get(self.test_url, proxy=proxy_url, timeout=self.timeout) as response:
                        data = await response.json()
                else:
                    async with session.get(self.test_url, timeout=self.timeout) as response:
                        data = await response.json()

                response_time = round((time.time() - start_time) * 1000, 2)  # in ms
                
                result = {
                    "proxy": proxy,
                    "status": "Working",
                    "response_time": response_time,
                    "ip": data.get("query", "Unknown"),
                    "country": data.get("country", "Unknown"),
                    "type": proxy_type.upper()
                }
                self.working_proxies.append(proxy)

        except Exception as e:
            result = {
                "proxy": original_proxy,
                "status": f"Failed: {str(e)[:50]}...",
                "response_time": None,
                "ip": None,
                "country": None,
                "type": "Unknown"
            }
            self.failed_proxies.append(original_proxy)

        self.results.append(result)
        return result

    def _detect_protocol(self, proxy: str) -> str:
        """Auto-prepend protocol based on common proxy ports"""
        if ":" in proxy:
            host, port = proxy.rsplit(":", 1)
            if port in ['1080', '1081']:
                return f"socks5://{proxy}"
        return f"http://{proxy}"

    def _create_error_result(self, proxy: str, error: str):
        return {
            "proxy": proxy,
            "status": f"Failed ({error[:30]})",
            "response_time": None,
            "ip": None,
            "country": None,
            "type": self._get_proxy_type(proxy),
            "attempts": self.retries + 1
        }

    def load_proxies(self) -> List[str]:
        with open(self.proxy_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    async def check_all_proxies(self):
        proxies = self.load_proxies()
        with Progress() as progress:
            task = progress.add_task("[cyan]Checking proxies...", total=len(proxies))
            
            # Create all tasks at once
            tasks = [self.check_proxy(proxy) for proxy in proxies]
            
            # Use completed callback for progress updates
            completed = 0
            for future in asyncio.as_completed(tasks):
                await future
                completed += 1
                progress.update(task, completed=completed)

    def save_working_proxies(self):
        with open('working_proxies.txt', 'w') as f:
            for proxy in self.working_proxies:
                f.write(f"{proxy}\n")

    def save_failed_proxies(self):
        with open('failed_proxies.txt', 'w') as f:
            for proxy in self.failed_proxies:
                f.write(f"{proxy}\n")

    def save_results(self, format: str = "txt"):
        if format == "json":
            with open('results.json', 'w') as f:
                json.dump(self.results, f, indent=2)
        elif format == "csv":
            with open('results.csv', 'w') as f:
                f.write("Proxy,Type,Status,Response Time,IP,Country\n")
                for result in self.results:
                    f.write(f"{result['proxy']},{result['type']},{result['status']},"
                            f"{result['response_time'] or ''},{result['ip'] or ''},"
                            f"{result['country'] or ''}\n")
        # Existing txt format saving remains

    def print_results(self):
        # Sort results by response time (fastest first)
        self.results.sort(key=lambda x: x["response_time"] or float('inf'))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Proxy")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Response Time (ms)")
        table.add_column("IP")
        table.add_column("Country")

        for result in self.results:
            status_color = "green" if result["status"] == "Working" else "red"
            table.add_row(
                result["proxy"],
                result["type"],
                f"[{status_color}]{result['status']}[/{status_color}]",
                str(result["response_time"]) if result["response_time"] else "N/A",
                str(result["ip"]) if result["ip"] else "N/A",
                str(result["country"]) if result["country"] else "N/A"
            )

        console.print("\n[bold]Proxy Checking Results:[/bold]")
        console.print(table)
        console.print(f"\n[green]Working proxies saved to working_proxies.txt[/green]")
        console.print(f"[red]Failed proxies saved to failed_proxies.txt[/red]")

async def main():
    console.print("[bold blue]Starting Proxy Checker...[/bold blue]")
    checker = ProxyChecker("proxies.txt")
    await checker.check_all_proxies()
    checker.save_working_proxies()
    checker.save_failed_proxies()
    checker.save_results()
    checker.print_results()

if __name__ == "__main__":
    asyncio.run(main()) 
