# Custom scripts and projects

The `project.yml` lets you define any custom commands and run them as part of
your training, evaluation or deployment workflows. The `script` section defines
a list of commands that are called in a subprocess, in order. This lets you
execute other Python scripts or command-line tools. Let's say you've written a
few integration tests that load the best model produced by the training command
and check that it works correctly. You can now define a `test` command that
calls into [`pytest`](https://docs.pytest.org/en/latest/), runs your tests and
uses [`pytest-html`](https://github.com/pytest-dev/pytest-html) to export a test
report:

```yaml {title="project.yml"}
commands:
  - name: test
    help: 'Test the trained pipeline'
    script:
      - 'pip install pytest pytest-html'
      - 'python -m pytest ./scripts/tests --html=metrics/test-report.html'
    deps:
      - 'training/model-best'
    outputs:
      - 'metrics/test-report.html'
    no_skip: true
```

Adding `training/model-best` to the command's `deps` lets you ensure that the
file is available. If not, spaCy will show an error and the command won't run.
Setting `no_skip: true` means that the command will always run, even if the
dependencies (the trained pipeline) haven't changed. This makes sense here,
because you typically don't want to skip your tests.

## Writing custom scripts

Your project commands can include any custom scripts – essentially, anything you
can run from the command line. Here's an example of a custom script that uses
[`typer`](https://typer.tiangolo.com/) for quick and easy command-line arguments
that you can define via your `project.yml`:

> #### About Typer
>
> [`typer`](https://typer.tiangolo.com/) is a modern library for building Python
> CLIs using type hints. It's a dependency of spaCy, so it will already be
> pre-installed in your environment. Function arguments automatically become
> positional CLI arguments and using Python type hints, you can define the value
> types. For instance, `batch_size: int` means that the value provided via the
> command line is converted to an integer.

```python {title="scripts/custom_evaluation.py"}
import typer

def custom_evaluation(batch_size: int = 128, model_path: str, data_path: str):
    # The arguments are now available as positional CLI arguments
    print(batch_size, model_path, data_path)

if __name__ == "__main__":
    typer.run(custom_evaluation)
```

In your `project.yml`, you can then run the script by calling
`python scripts/custom_evaluation.py` with the function arguments. You can also
use the `vars` section to define reusable variables that will be substituted in
commands, paths and URLs. In this example, the batch size is defined as a
variable will be added in place of `${vars.batch_size}` in the script. Just like
in the [training config](/usage/training##config-overrides), you can also
override settings on the command line – for example using `--vars.batch_size`.

> #### Calling into Python
>
> If any of your command scripts call into `python`, spaCy will take care of
> replacing that with your `sys.executable`, to make sure you're executing
> everything with the same Python (not some other Python installed on your
> system). It also normalizes references to `python3`, `pip3` and `pip`.

{/*prettier-ignore*/}

```yaml {title="project.yml"}
vars:
  batch_size: 128

commands:
  - name: evaluate
    script:
      - 'python scripts/custom_evaluation.py ${vars.batch_size} ./training/model-best ./corpus/eval.json'
    deps:
      - 'training/model-best'
      - 'corpus/eval.json'
```

You can also use the `env` section to reference **environment variables** and
make their values available to the commands. This can be useful for overriding
settings on the command line and passing through system-level settings.

> #### Usage example
>
> ```bash
> export GPU_ID=1
> BATCH_SIZE=128 python -m spacy project run evaluate
> ```

```yaml {title="project.yml"}
env:
  batch_size: BATCH_SIZE
  gpu_id: GPU_ID

commands:
  - name: evaluate
    script:
      - 'python scripts/custom_evaluation.py ${env.batch_size}'
```

## Documenting your project

> #### Readme Example
>
> For more examples, see the [`projects`](https://github.com/explosion/projects)
> repo.
>
> ![Screenshot of auto-generated Markdown Readme](assets/project_document.jpg)

When your custom project is ready and you want to share it with others, you can
use the [`spacy project document`](/api/cli#project-document) command to
**auto-generate** a pretty, Markdown-formatted `README` file based on your
project's `project.yml`. It will list all commands, workflows and assets defined
in the project and include details on how to run the project, as well as links
to the relevant spaCy documentation to make it easy for others to get started
using your project.

```bash
python -m spacy project document --output README.md
```

Under the hood, hidden markers are added to identify where the auto-generated
content starts and ends. This means that you can add your own custom content
before or after it and re-running the `project document` command will **only
update the auto-generated part**. This makes it easy to keep your documentation
up to date.

<Infobox variant="warning">

Note that the contents of an existing file will be **replaced** if no existing
auto-generated docs are found. If you want spaCy to ignore a file and not update
it, you can add the comment marker `{/* SPACY PROJECT: IGNORE */}` anywhere in
your markup.

</Infobox>

## Cloning from your own repo

The [`spacy project clone`](/api/cli#project-clone) command lets you customize
the repo to clone from using the `--repo` option. It calls into `git`, so you'll
be able to clone from any repo that you have access to, including private repos.

```bash
python -m spacy project clone your_project --repo https://github.com/you/repo
```

At a minimum, a valid project template needs to contain a
[`project.yml`](#project-yml). It can also include
[other files](/usage/projects#project-files), like custom scripts, a
`requirements.txt` listing additional dependencies,
[training configs](/usage/training#config) and model meta templates, or Jupyter
notebooks with usage examples.

<Infobox title="Important note about assets" variant="warning">

It's typically not a good idea to check large data assets, trained pipelines or
other artifacts into a Git repo and you should exclude them from your project
template by adding a `.gitignore`. If you want to version your data and models,
check out [Data Version Control](#dvc) (DVC), which integrates with spaCy
projects.

</Infobox>

# Remote Storage

You can persist your project outputs to a remote storage using the
[`project push`](/api/cli#project-push) command. This can help you **export**
your pipeline packages, **share** work with your team, or **cache results** to
avoid repeating work. The [`project pull`](/api/cli#project-pull) command will
download any outputs that are in the remote storage and aren't available
locally.

You can list one or more remotes in the `remotes` section of your
[`project.yml`](#project-yml) by mapping a string name to the URL of the
storage. Under the hood, spaCy uses
[`Pathy`](https://github.com/justindujardin/pathy) to communicate with the
remote storages, so you can use any protocol that `Pathy` supports, including
[S3](https://aws.amazon.com/s3/),
[Google Cloud Storage](https://cloud.google.com/storage), and the local
filesystem, although you may need to install extra dependencies to use certain
protocols.

> #### Example
>
> ```bash
> $ python -m spacy project pull local
> ```

```yaml {title="project.yml"}
remotes:
  default: 's3://my-spacy-bucket'
  local: '/mnt/scratch/cache'
```

<Infobox title="How it works" emoji="💡">

Inside the remote storage, spaCy uses a clever **directory structure** to avoid
overwriting files. The top level of the directory structure is a URL-encoded
version of the output's path. Within this directory are subdirectories named
according to a hash of the command string and the command's dependencies.
Finally, within those directories are files, named according to an MD5 hash of
their contents.

{/*TODO: update with actual real example?*/}

{/*prettier-ignore*/}

```yaml
└── urlencoded_file_path            # Path of original file
    ├── some_command_hash           # Hash of command you ran
    │   ├── some_content_hash       # Hash of file content
    │   └── another_content_hash
    └── another_command_hash
        └── third_content_hash
```

</Infobox>

For instance, let's say you had the following command in your `project.yml`:

```yaml {title="project.yml"}
- name: train
  help: 'Train a spaCy pipeline using the specified corpus and config'
  script:
    - 'spacy train ./config.cfg --output training/'
  deps:
    - 'corpus/train'
    - 'corpus/dev'
    - 'config.cfg'
  outputs:
    - 'training/model-best'
```

> #### Example
>
> ```
> └── s3://my-spacy-bucket/training%2Fmodel-best
>     └── 1d8cb33a06cc345ad3761c6050934a1b
>         └── d8e20c3537a084c5c10d95899fe0b1ff
> ```

After you finish training, you run [`project push`](/api/cli#project-push) to
make sure the `training/model-best` output is saved to remote storage. spaCy
will then construct a hash from your command script and the listed dependencies,
`corpus/train`, `corpus/dev` and `config.cfg`, in order to identify the
execution context of your output. It would then compute an MD5 hash of the
`training/model-best` directory, and use those three pieces of information to
construct the storage URL.

```bash
python -m spacy project run train
python -m spacy project push
```

If you change the command or one of its dependencies (for instance, by editing
the [`config.cfg`](/usage/training#config) file to tune the hyperparameters, a
different creation hash will be calculated, so when you use
[`project push`](/api/cli#project-push) you won't be overwriting your previous
file. The system even supports multiple outputs for the same file and the same
context, which can happen if your training process is not deterministic, or if
you have dependencies that aren't represented in the command.

In summary, the [`weasel`](/api/cli#project) remote storages are designed
to make a particular set of trade-offs. Priority is placed on **convenience**,
**correctness** and **avoiding data loss**. You can use
[`project push`](/api/cli#project-push) freely, as you'll never overwrite remote
state, and you don't have to come up with names or version numbers. However,
it's up to you to manage the size of your remote storage, and to remove files
that are no longer relevant to you.
