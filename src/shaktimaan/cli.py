import typer

from shaktimaan import __version__

app = typer.Typer(
    name="shaktimaan",
    help="A personal Spec-Driven Development (SDD) CLI toolkit for Claude Code.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"shaktimaan {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the shaktimaan version and exit.",
    ),
) -> None:
    """Shaktimaan: scaffold a spec-driven-development workflow into your project."""


def main() -> None:
    app()
