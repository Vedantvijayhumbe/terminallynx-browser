import os
import sys
import requests
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()
load_dotenv()

class GeminiBrowser:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            console.print("[bold red]API key not set in .env[/bold red]")
            sys.exit(1)
        self.model = "gemini-1.5-flash"
        self.system_prompt = None

    def set_model(self, model_name):
        supported_models = ['gemini-1.5-flash', 'gemini-1.5-pro']
        if model_name in supported_models:
            self.model = model_name
            console.print(f"[cyan]Switched to model:[/cyan] [bold]{model_name}[/bold]")
        else:
            console.print("[red]Unsupported model.[/red] Available models: "
                          + ', '.join(supported_models))

    def gemini_query(self, prompt, retries=3, delay=2):
        api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        headers = {"Content-Type": "application/json"}

        content = [{"parts": [{"text": prompt}]}]
        if self.system_prompt:
            content.insert(0, {"parts": [{"text": f"[SYSTEM]: {self.system_prompt}"}]})

        data = {"contents": content}

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(api_url, json=data, headers=headers, timeout=30)
                if response.status_code == 200:
                    output = response.json()
                    try:
                        return output["candidates"][0]["content"]["parts"][0]["text"].strip()
                    except (KeyError, IndexError):
                        return "⚠️ No valid response from Gemini."
                else:
                    console.print(f"[bold red]Error {response.status_code}[/bold red]: {response.text}")
                    if 500 <= response.status_code < 600 and attempt < retries:
                        time.sleep(delay)
                        continue
                    return None
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Request failed:[/bold red] {e}")
                if attempt < retries:
                    time.sleep(delay)
                    continue
                return None


def main():
    bot = GeminiBrowser()
    console.print(Panel("[bold cyan]Welcome to the Gemini CLI Browser[/bold cyan]\n"
                        "Type [yellow]exit[/yellow] to quit\n"
                        "Type [yellow]/help[/yellow] for commands",
                        title="Info", style="blue"))

    last_reply = None
    history = []  # (user_input, reply)

    while True:
        user_input = Prompt.ask("[bold green]>>>[/bold green]").strip()

        if user_input.lower() in ["exit", "quit"]:
            console.print("[bold red]Goodbye![/bold red]")
            break

        elif user_input.startswith('/help'):
            help_text = Table(title="Available Commands")
            help_text.add_column("Command", style="cyan")
            help_text.add_column("Description", style="green")
            help_text.add_row("/model NAME", "Switch model (gemini-1.5-flash / gemini-1.5-pro)")
            help_text.add_row("/save file.txt", "Save last reply to file")
            help_text.add_row("/export file.txt", "Export full conversation to file")
            help_text.add_row("/history", "Show past conversation")
            help_text.add_row("/system TEXT", "Set a system instruction/persona")
            help_text.add_row("/help", "Show this help menu")
            help_text.add_row("exit/quit", "Exit the program")
            console.print(help_text)

        elif user_input.startswith('/model'):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                bot.set_model(parts[1].strip())
            else:
                console.print("[yellow]Usage:[/yellow] /model MODEL_NAME")

        elif user_input.startswith('/save'):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                filename = parts[1].strip()
                if last_reply:
                    try:
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(last_reply)
                        console.print(f"[bold green]Reply saved to {filename}[/bold green]")
                    except Exception as e:
                        console.print(f"[bold red]Error saving file:[/bold red] {e}")
                else:
                    console.print("[yellow]No reply to save yet.[/yellow]")
            else:
                console.print("[yellow]Usage:[/yellow] /save filename.txt")

        elif user_input.startswith('/export'):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                filename = parts[1].strip()
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        for q, r in history:
                            f.write(f"USER: {q}\nGEMINI: {r}\n\n")
                    console.print(f"[bold green]Conversation exported to {filename}[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Error exporting file:[/bold red] {e}")
            else:
                console.print("[yellow]Usage:[/yellow] /export filename.txt")

        elif user_input.startswith('/history'):
            if not history:
                console.print("[yellow]No history yet.[/yellow]")
            else:
                for i, (q, r) in enumerate(history, 1):
                    console.print(Panel(f"[bold yellow]You:[/bold yellow] {q}\n\n"
                                        f"[bold green]Gemini:[/bold green] {r}",
                                        title=f"Exchange {i}", style="magenta"))

        elif user_input.startswith('/system'):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                bot.system_prompt = parts[1].strip()
                console.print(f"[cyan]System instruction set:[/cyan] {bot.system_prompt}")
            else:
                console.print("[yellow]Usage:[/yellow] /system TEXT")

        else:
            with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                reply = bot.gemini_query(user_input)

            if reply:
                console.print(Panel(reply, title="Gemini Reply", style="green"))
                last_reply = reply
                history.append((user_input, reply))


if __name__ == "__main__":
    main()
