# Integrations

## Data Version Control (DVC)

Data assets like training corpora or pretrained weights are at the core of any
NLP project, but they're often difficult to manage: you can't just check them
into your Git repo to version and keep track of them. And if you have multiple
steps that depend on each other, like a preprocessing step that generates your
training data, you need to make sure the data is always up-to-date, and re-run
all steps of your process every time, just to be safe.

[Data Version Control](https://dvc.org) (DVC) is a standalone open-source tool
that integrates into your workflow like Git, builds a dependency graph for your
data pipelines and tracks and caches your data files. If you're downloading data
from an external source, like a storage bucket, DVC can tell whether the
resource has changed. It can also determine whether to re-run a step, depending
on whether its input have changed or not. All metadata can be checked into a Git
repo, so you'll always be able to reproduce your experiments.

To set up DVC, install the package and initialize your spaCy project as a Git
and DVC repo. You can also
[customize your DVC installation](https://dvc.org/doc/install/macos#install-with-pip)
to include support for remote storage like Google Cloud Storage, S3, Azure, SSH
and more.

```bash
pip install dvc   # Install DVC
git init          # Initialize a Git repo
dvc init          # Initialize a DVC project
```

> :warning: **Important note on privacy**
>
> DVC enables usage analytics by default, so if you're working in a
> privacy-sensitive environment, make sure to
> [**opt-out manually**](https://dvc.org/doc/user-guide/analytics#opting-out).

The [`weasel dvc`](../cli.md#dvc) command creates a `dvc.yaml`
config file based on a workflow defined in your `project.yml`. Whenever you
update your project, you can re-run the command to update your DVC config. You
can then manage your spaCy project like any other DVC project, run
[`dvc add`](https://dvc.org/doc/command-reference/add) to add and track assets
and [`dvc repro`](https://dvc.org/doc/command-reference/repro) to reproduce the
workflow or individual commands.

```bash
python -m weasel dvc [project_dir] [workflow_name]
```

> :warning: **Important note for multiple workflows**
>
> DVC currently expects a single workflow per project, so when creating the config
> with [`weasel dvc`](../cli.md#dvc), you need to specify the name
> of a workflow defined in your `project.yml`. You can still use multiple
> workflows, but only one can be tracked by DVC.
