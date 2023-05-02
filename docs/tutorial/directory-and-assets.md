# Project directory and assets

## project.yml

The `project.yml` defines the assets a project depends on, like datasets and
pretrained weights, as well as a series of commands that can be run separately
or as a workflow – for instance, to preprocess the data, convert it to spaCy's
format, train a pipeline, evaluate it and export metrics, package it and spin up
a quick web demo. It looks pretty similar to a config file used to define CI
pipelines.

> #### Tip: Multi-line YAML syntax for long values
>
> YAML has [multi-line syntax](https://yaml-multiline.info/) that can be helpful
> for readability with longer values such as project descriptions or commands
> that take several arguments.

```yaml
%%GITHUB_PROJECTS/pipelines/tagger_parser_ud/project.yml
```

> #### Tip: Overriding variables on the CLI
>
> If you want to override one or more variables on the CLI and are not already
> specifying a project directory, you need to add `.` as a placeholder:
>
> ```
> python -m spacy project run test . --vars.foo bar
> ```

> #### Tip: Environment Variables
>
> Commands in a project file are not executed in a shell, so they don't have
> direct access to environment variables. But you can insert environment
> variables using the `env` dictionary to make values available for
> interpolation, just like values in `vars`. Here's an example `env` dict that
> makes `$PATH` available as `ENV_PATH`:
>
> ```yaml
> env:
>   ENV_PATH: PATH
> ```
>
> This can be used in a project command like so:
>
> ```yaml
> - name: 'echo-path'
>   script:
>     - 'echo ${env.ENV_PATH}'
> ```

| Section                                             | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `title`                                             | An optional project title used in `--help` message and [auto-generated docs](#custom-docs).                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `description`                                       | An optional project description used in [auto-generated docs](#custom-docs).                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `vars`                                              | A dictionary of variables that can be referenced in paths, URLs and scripts and overriden on the CLI, just like [`config.cfg` variables](/usage/training#config-interpolation). For example, `${vars.name}` will use the value of the variable `name`. Variables need to be defined in the section `vars`, but can be a nested dict, so you're able to reference `${vars.model.name}`.                                                                                                                       |
| `env`                                               | A dictionary of variables, mapped to the names of environment variables that will be read in when running the project. For example, `${env.name}` will use the value of the environment variable defined as `name`.                                                                                                                                                                                                                                                                                          |
| `directories`                                       | An optional list of [directories](#project-files) that should be created in the project for assets, training outputs, metrics etc. spaCy will make sure that these directories always exist.                                                                                                                                                                                                                                                                                                                 |
| `assets`                                            | A list of assets that can be fetched with the [`project assets`](/api/cli#project-assets) command. `url` defines a URL or local path, `dest` is the destination file relative to the project directory, and an optional `checksum` ensures that an error is raised if the file's checksum doesn't match. Instead of `url`, you can also provide a `git` block with the keys `repo`, `branch` and `path`, to download from a Git repo.                                                                        |
| `workflows`                                         | A dictionary of workflow names, mapped to a list of command names, to execute in order. Workflows can be run with the [`project run`](/api/cli#project-run) command.                                                                                                                                                                                                                                                                                                                                         |
| `commands`                                          | A list of named commands. A command can define an optional help message (shown in the CLI when the user adds `--help`) and the `script`, a list of commands to run. The `deps` and `outputs` let you define the created file the command depends on and produces, respectively. This lets spaCy determine whether a command needs to be re-run because its dependencies or outputs changed. Commands can be run as part of a workflow, or separately with the [`project run`](/api/cli#project-run) command. |
| `spacy_version`                                     | Optional spaCy version range like `>=3.0.0,<3.1.0` that the project is compatible with. If it's loaded with an incompatible version, an error is raised when the project is loaded.                                                                                                                                                                                                                                                                                                                          |
| `check_requirements` <Tag variant="new">3.4.2</Tag> | A flag determining whether to verify that the installed dependencies align with the project's `requirements.txt`. Defaults to `true`.                                                                                                                                                                                                                                                                                                                                                                        |

## Data assets

Assets are any files that your project might need, like training and development
corpora or pretrained weights for initializing your model. Assets are defined in
the `assets` block of your `project.yml` and can be downloaded using the
[`project assets`](/api/cli#project-assets) command. Defining checksums lets you
verify that someone else running your project will use the same files you used.
Asset URLs can be a number of different **protocols**: HTTP, HTTPS, FTP, SSH,
and even **cloud storage** such as GCS and S3. You can also download assets from
a **Git repo** instead.

### Downloading from a URL or cloud storage

Under the hood, spaCy uses the
[`smart-open`](https://github.com/RaRe-Technologies/smart_open) library so you
can use any protocol it supports. Note that you may need to install extra
dependencies to use certain protocols.

> #### project.yml
>
> ```yaml
> assets:
>   # Download from public HTTPS URL
>   - dest: 'assets/training.spacy'
>     url: 'https://example.com/data.spacy'
>     checksum: '63373dd656daa1fd3043ce166a59474c'
>   # Optional download from Google Cloud Storage bucket
>   - dest: 'assets/development.spacy'
>     extra: True
>     url: 'gs://your-bucket/corpora'
>     checksum: '5113dc04e03f079525edd8df3f4f39e3'
> ```

| Name          | Description                                                                                                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dest`        | The destination path to save the downloaded asset to (relative to the project directory), including the file name.                                                               |
| `extra`       | Optional flag determining whether this asset is downloaded only if `spacy project assets` is run with `--extra`. `False` by default.                                             |
| `url`         | The URL to download from, using the respective protocol.                                                                                                                         |
| `checksum`    | Optional checksum of the file. If provided, it will be used to verify that the file matches and downloads will be skipped if a local file with the same checksum already exists. |
| `description` | Optional asset description, used in [auto-generated docs](#custom-docs).                                                                                                         |

### Downloading from a Git repo

If a `git` block is provided, the asset is downloaded from the given Git
repository. You can download from any repo that you have access to. Under the
hood, this uses Git's "sparse checkout" feature, so you're only downloading the
files you need and not the whole repo.

> #### project.yml
>
> ```yaml
> assets:
>   - dest: 'assets/training.spacy'
>     git:
>       repo: 'https://github.com/example/repo'
>       branch: 'master'
>       path: 'path/training.spacy'
>     checksum: '63373dd656daa1fd3043ce166a59474c'
>     description: 'The training data (5000 examples)'
> ```

| Name          | Description                                                                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dest`        | The destination path to save the downloaded asset to (relative to the project directory), including the file name.                                                                                                                    |
| `git`         | `repo`: The URL of the repo to download from.<br />`path`: Path of the file or directory to download, relative to the repo root. "" specifies the root directory.<br />`branch`: The branch to download from. Defaults to `"master"`. |
| `checksum`    | Optional checksum of the file. If provided, it will be used to verify that the file matches and downloads will be skipped if a local file with the same checksum already exists.                                                      |
| `description` | Optional asset description, used in [auto-generated docs](#custom-docs).                                                                                                                                                              |

### Working with private assets

> #### project.yml
>
> ```yaml
> assets:
>   - dest: 'assets/private_training_data.json'
>     checksum: '63373dd656daa1fd3043ce166a59474c'
>   - dest: 'assets/private_vectors.bin'
>     checksum: '5113dc04e03f079525edd8df3f4f39e3'
> ```

For many projects, the datasets and weights you're working with might be
company-internal and not available over the internet. In that case, you can
specify the destination paths and a checksum, and leave out the URL. When your
teammates clone and run your project, they can place the files in the respective
directory themselves. The [`project assets`](/api/cli#project-assets) command
will alert you about missing files and mismatched checksums, so you can ensure
that others are running your project with the same data.

## Dependencies and outputs

Each command defined in the `project.yml` can optionally define a list of
dependencies and outputs. These are the files the command requires and creates.
For example, a command for training a pipeline may depend on a
[`config.cfg`](/usage/training#config) and the training and evaluation data, and
it will export a directory `model-best`, which you can then re-use in other
commands.

{/*prettier-ignore*/}

```yaml {title="project.yml"}
commands:
  - name: train
    help: 'Train a spaCy pipeline using the specified corpus and config'
    script:
      - 'python -m spacy train ./configs/config.cfg -o training/ --paths.train ./corpus/training.spacy --paths.dev ./corpus/evaluation.spacy'
    deps:
      - 'configs/config.cfg'
      - 'corpus/training.spacy'
      - 'corpus/evaluation.spacy'
    outputs:
      - 'training/model-best'
```

> #### Re-running vs. skipping
>
> Under the hood, spaCy uses a `project.lock` lockfile that stores the details
> for each command, as well as its dependencies and outputs and their checksums.
> It's updated on each run. If any of this information changes, the command will
> be re-run. Otherwise, it will be skipped.

If you're running a command and it depends on files that are missing, spaCy will
show you an error. If a command defines dependencies and outputs that haven't
changed since the last run, the command will be skipped. This means that you're
only re-running commands if they need to be re-run. Commands can also set
`no_skip: true` if they should never be skipped – for example commands that run
tests. Commands without outputs are also never skipped. To force re-running a
command or workflow, even if nothing changed, you can set the `--force` flag.

Note that [`weasel`](/api/cli#project) doesn't compile any dependency
graphs based on the dependencies and outputs, and won't re-run previous steps
automatically. For instance, if you only run the command `train` that depends on
data created by `preprocess` and those files are missing, spaCy will show an
error – it won't just re-run `preprocess`. If you're looking for more advanced
data management, check out the [Data Version Control (DVC) integration](#dvc).
If you're planning on integrating your Weasel project with DVC, you can also use
`outputs_no_cache` instead of `outputs` to define outputs that won't be cached
or tracked.

## Files and directory structure

The `project.yml` can define a list of `directories` that should be created
within a project – for instance, `assets`, `training`, `corpus` and so on. spaCy
will make sure that these directories are always available, so your commands can
write to and read from them. Project directories will also include all files and
directories copied from the project template with
[`spacy project clone`](/api/cli#project-clone). Here's an example of a project
directory:

> #### project.yml
>
> {/*prettier-ignore*/}
>
> ```yaml
> directories: ['assets', 'configs', 'corpus', 'metas', 'metrics', 'notebooks', 'packages', 'scripts', 'training']
> ```

```yaml {title="Example project directory"}
├── project.yml          # the project settings
├── project.lock         # lockfile that tracks inputs/outputs
├── assets/              # downloaded data assets
├── configs/             # pipeline config.cfg files used for training
├── corpus/              # output directory for training corpus
├── metas/               # pipeline meta.json templates used for packaging
├── metrics/             # output directory for evaluation metrics
├── notebooks/           # directory for Jupyter notebooks
├── packages/            # output directory for pipeline Python packages
├── scripts/             # directory for scripts, e.g. referenced in commands
├── training/            # output directory for trained pipelines
└── ...                  # any other files, like a requirements.txt etc.
```

If you don't want a project to create a directory, you can delete it and remove
its entry from the `project.yml` – just make sure it's not required by any of
the commands. [Custom templates](#custom) can use any directories they need –
the only file that's required for a project is the `project.yml`.

---

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
