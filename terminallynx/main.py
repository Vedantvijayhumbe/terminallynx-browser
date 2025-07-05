import asyncio
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.prompt import Prompt

try:
    from pyppeteer import launch
    JS_ENABLED = True
except ImportError:
    JS_ENABLED = False

console = Console()

class TerminalBrowser:
    def __init__(self, enable_js=False):
        self.history = []
        self.current_url = None
        self.enable_js = enable_js and JS_ENABLED

    async def get_rendered_html(self, url):
        browser = await launch(headless=True, args=['--no-sandbox'])
        page = await browser.newPage()
        await page.goto(url, {'waitUntil': 'networkidle2'})
        content = await page.content()
        await browser.close()
        return content

    def fetch_page(self, url):
        try:
            if self.enable_js:
                html = asyncio.get_event_loop().run_until_complete(self.get_rendered_html(url))
            else:
                response = requests.get(url)
                response.raise_for_status()
                html = response.text
            return html
        except Exception as e:
            console.print(f"[red]Failed to fetch {url}: {e}[/red]")
            return ""

    def render_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        console.rule("📰 Page Content")
        console.print(soup.get_text(), style="green")

        links = soup.find_all('a')
        self.link_map = {}

        if links:
            console.rule("🔗 Links")
            for i, link in enumerate(links):
                href = link.get('href')
                if href and href.startswith('http'):
                    console.print(f"[{i}] {link.get_text()} -> {href}", style="cyan")
                    self.link_map[str(i)] = href

    def start(self):
        console.print("🌐 [bold yellow]Welcome to TerminalLynx[/bold yellow]", style="bold")
        if self.enable_js:
            console.print("⚙️  JavaScript rendering is enabled")
        else:
            console.print("🛑 JavaScript rendering is disabled or pyppeteer not found")

        while True:
            url = Prompt.ask("Enter URL (or 'back', 'exit')")

            if url.lower() == 'exit':
                break
            elif url.lower() == 'back' and self.history:
                url = self.history.pop()
            elif self.current_url:
                self.history.append(self.current_url)

            self.current_url = url
            html = self.fetch_page(url)
            if html:
                self.render_text(html)
                self.handle_navigation()

    def handle_navigation(self):
        choice = Prompt.ask("➡️  Enter link number to follow (or press Enter to stay)", default="")
        if choice in self.link_map:
            self.start_link(self.link_map[choice])

    def start_link(self, link):
        self.history.append(self.current_url)
        self.current_url = link
        html = self.fetch_page(link)
        if html:
            self.render_text(html)
            self.handle_navigation()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="TerminalLynx - A terminal web browser with optional JavaScript support")
    parser.add_argument('--enable-js', action='store_true', help='Enable JavaScript rendering (requires pyppeteer)')
    args = parser.parse_args()

    browser = TerminalBrowser(enable_js=args.enable_js)
    browser.start()

if __name__ == '__main__':
    main()