import asyncio
import os

from dotenv import find_dotenv, load_dotenv
from google import genai
from rich.align import Align
from rich.panel import Panel
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, RichLog

MODEL_NAME = "gemini-2.5-flash"
SYSTEM_PROMPT = """
You are now operating within a Python Textual TUI Application.
Your output will be displayed in a terminal interface, which uses a tag syntax for formatting.
For example,
[bold]This text is bold[/]
[italic]This text is italic[/]
[bold]Bold [italic]Bold and italic[/italic][/]
[underline]This text is underlined[/]
[red]This text is red[/] 
[#ff0000]HTML hex style[/]
[rgba(0,255,0)]HTML RGB style[/]
[red 50%]This is in faded red[/]
[on #ff0000]Background is bright red.
[on #ff0000 20%]The background has a red tint.[/]
[link="https://www.willmcgugan.com"]A link to a blog[/link]
Avoid using *, # symbols, or other markdown syntax.
Do not output Markdown or HTML.
Use these tags to format your responses appropriately for display in the terminal interface.
Respond to the user in a fast, concise and clear manner.
""".strip()


class ChatApp(App):
    CSS = """
    #input { dock: bottom; }
    """

    def __init__(self):
        super().__init__()
        load_dotenv(dotenv_path=find_dotenv())

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        if GEMINI_API_KEY is None:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set\nPlease set a valid API key"
            )

        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.chat = self.client.chats.create(
            model=MODEL_NAME,
            history=[{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}],
        )

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(markup=True, id="chatlog")
        yield Input(placeholder="Type your message...", id="input")
        yield Footer()

    async def on_mount(self) -> None:
        self.log_sys("Chat started.\n")
        self.query_one("#input", Input).focus()

    def log_sys(self, text: str) -> None:
        msg = Align(
            Panel(
                text,
                title="[yellow]System[/]",
                title_align="center",
                width=max(self.console.width // 3, 60),
            ),
            "center",
        )
        self.query_one(RichLog).write(msg, expand=True)

    def log_user(self, text: str) -> None:
        msg = Align(
            Panel(
                text,
                title="[green]You[/]",
                title_align="right",
                width=max(self.console.width // 3, 60),
            ),
            "right",
        )
        self.query_one(RichLog).write(msg, expand=True)

    def log_bot(self, text: str) -> None:
        msg = Align(
            Panel(
                text,
                title="[blue]Gemini[/]",
                title_align="left",
                width=max(self.console.width // 3, 60),
            ),
            "left",
        )
        
        self.query_one(RichLog).write(msg, expand=True)

    @on(Input.Submitted, "#input")
    async def handle_submit(self, event: Input.Submitted):
        prompt = event.value.strip()

        self.query_one("#input", Input).value = ""

        if not prompt:
            return

        self.log_user(prompt)

        input_box = self.query_one("#input", Input)
        input_box.disabled = True


        if self.chat is None:
            self.log_sys("[red]Chat session not initialized.[/]")
            return

        try:
            response = await asyncio.to_thread(self.chat.send_message, prompt)
            self.log_bot(response.text)  # type: ignore
        except Exception as e:
            self.log_sys(f"[red]Error: {e}[/]")
        finally:
            input_box.disabled = False
            input_box.focus()


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
