import uuid
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from async_context_engine import AsyncPoller
from graph import graph, store

console = Console()

config = {"configurable": {"thread_id": f"session-{uuid.uuid4().hex[:8]}"}}


def display_output(output: dict) -> None:
    """Callback for the poller — renders graph output in the terminal."""
    if "conductor" in output:
        msg = output["conductor"]["messages"][-1]
        content = msg.content if hasattr(msg, "content") else msg.get("content", "")
        console.print(
            Panel(content, title="[bold magenta]Conductor[/bold magenta]", border_style="magenta")
        )


def main():
    console.print()
    console.print(
        Panel(
            "[bold cyan]Async Context Engine[/bold cyan]\n"
            "[dim]Context-aware async task orchestration powered by LangGraph[/dim]",
            border_style="cyan",
            subtitle="v4.0",
        )
    )
    console.print("[dim]Type your messages. Async tasks run in the background.[/dim]")
    console.print("[dim]Type 'quit' to exit.[/dim]\n")

    poller = AsyncPoller(store=store, graph=graph, config=config, interval=5, on_result=display_output)
    poller.start()

    while True:
        try:
            user_input = console.input("[bold yellow]You:[/bold yellow] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break

        for output in graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
        ):
            if "conductor" in output:
                msg = output["conductor"]["messages"][-1]
                content = msg.content if hasattr(msg, "content") else msg.get("content", "")
                console.print(
                    Panel(content, title="[bold magenta]Conductor[/bold magenta]", border_style="magenta")
                )
            elif "dispatcher" in output:
                msg = output["dispatcher"]["messages"][-1]
                content = msg.get("content", "") if isinstance(msg, dict) else msg.content
                console.print(
                    Panel(content, title="[bold blue]Dispatcher[/bold blue]", border_style="blue", subtitle="task queued")
                )

    poller.stop()
    console.print("\n[dim]Session ended. Goodbye![/dim]")


if __name__ == "__main__":
    main()
