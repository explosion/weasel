import typer

COMMAND = "python -m weasel"
NAME = "weasel"
HELP = """weasel Command-line Interface

DOCS: https://github.com/explosion/weasel
"""

PROJECT_FILE = "project.yml"
PROJECT_LOCK = "project.lock"

# Wrappers for Typer's annotations. Initially created to set defaults and to
# keep the names short, but not needed at the moment.
Arg = typer.Argument
Opt = typer.Option

app = typer.Typer(name=NAME, help=HELP, no_args_is_help=True)
