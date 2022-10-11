import typer

from .info import NAME, HELP
from .cli.clone import clone_cli

app = typer.Typer(name=NAME, help=HELP)
app.command("clone")(clone_cli)

@app.command("foobar", help="No-op")
def foobar():
    print("Just so that there are two commands")


if __name__ == "__main__":
    app()
