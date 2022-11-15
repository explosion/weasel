import typer

from .clone import clone_cli
from .document import document_cli
from .pull import pull_cli
from .push import push_cli
from .run import run_cli
from .assets import assets_cli
from ..info import HELP, NAME

app = typer.Typer(name=NAME, help=HELP, add_completion=False, no_args_is_help=True)
app.command("clone")(clone_cli)
app.command("document")(document_cli)
app.command("push")(push_cli)
app.command("pull")(pull_cli)
app.command("run")(run_cli)
app.command("assets")(assets_cli)


def exec_cli():

    app()
