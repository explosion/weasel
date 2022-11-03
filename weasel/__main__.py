import typer

from .cli.clone import clone_cli
from .cli.document import document_cli
from .cli.pull import pull_cli
from .cli.run import run_cli
from .info import HELP, NAME

app = typer.Typer(name=NAME, help=HELP, add_completion=False, no_args_is_help=True)
app.command("clone")(clone_cli)
app.command("document")(document_cli)
app.command("pull")(pull_cli)
app.command("run")(run_cli)


if __name__ == "__main__":
    app()
