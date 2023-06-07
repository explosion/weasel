# Project directory and assets

## `project.yml`

The `project.yml` defines the assets a project depends on, like datasets and
pretrained weights, as well as a series of commands that can be run separately
or as a workflow – for instance, to preprocess the data, convert it to Weasel's
format, train a pipeline, evaluate it and export metrics, package it and spin up
a quick web demo. It looks pretty similar to a config file used to define CI
pipelines.

> :boom: **Tip: Multi-line YAML**
>
> YAML has [multi-line syntax](https://yaml-multiline.info/) that can be helpful
> for readability with longer values such as project descriptions or commands
> that take several arguments.

> :boom: **Tip: Variable override**
>
> If you want to override one or more variables on the CLI and are not already
> specifying a project directory, you need to add `.` as a placeholder:
>
> ```
> python -m weasel run test . --vars.foo bar
> ```

> :boom: **Tip: Environment variables**
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

`project.yml` adheres to the following schema:

| Section              | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`              | An optional project title used in `--help` message and [auto-generated docs](../cli.md#closed_book-document).                                                                                                                                                                                                                                                                                                                                                                                         |
| `description`        | An optional project description used in [auto-generated docs](../cli.md#closed_book-document).                                                                                                                                                                                                                                                                                                                                                                                                        |
| `vars`               | A dictionary of variables that can be referenced in paths, URLs and scripts and overriden on the CLI, just like [`config.cfg` variables](https://spacy.io/usage/training#config-interpolation). For example, `${vars.name}` will use the value of the variable `name`. Variables need to be defined in the section `vars`, but can be a nested dict, so you're able to reference `${vars.model.name}`.                                                                                                |
| `env`                | A dictionary of variables, mapped to the names of environment variables that will be read in when running the project. For example, `${env.name}` will use the value of the environment variable defined as `name`.                                                                                                                                                                                                                                                                                   |
| `directories`        | An optional list of [directories](#data-assets) that should be created in the project for assets, training outputs, metrics etc. Weasel will make sure that these directories always exist.                                                                                                                                                                                                                                                                                                           |
| `assets`             | A list of assets that can be fetched with the [`assets`](../cli.md#open_file_folder-assets) command. `url` defines a URL or local path, `dest` is the destination file relative to the project directory, and an optional `checksum` ensures that an error is raised if the file's checksum doesn't match. Instead of `url`, you can also provide a `git` block with the keys `repo`, `branch` and `path`, to download from a Git repo.                                                               |
| `workflows`          | A dictionary of workflow names, mapped to a list of command names, to execute in order. Workflows can be run with the [`run`](../cli.md#rocket-run) command.                                                                                                                                                                                                                                                                                                                                          |
| `commands`           | A list of named commands. A command can define an optional help message (shown in the CLI when the user adds `--help`) and the `script`, a list of commands to run. The `deps` and `outputs` let you define the created file the command depends on and produces, respectively. This lets Weasel determine whether a command needs to be re-run because its dependencies or outputs changed. Commands can be run as part of a workflow, or separately with the [`run`](../cli.md#rocket-run) command. |
| `check_requirements` | A flag determining whether to verify that the installed dependencies align with the project's `requirements.txt`. Defaults to `true`.                                                                                                                                                                                                                                                                                                                                                                 |

## Data assets

Assets are any files that your project might need, like training and development
corpora or pretrained weights for initializing your model. Assets are defined in
the `assets` block of your `project.yml` and can be downloaded using the
[`assets`](../cli.md#open_file_folder-assets) command. Defining checksums lets you
verify that someone else running your project will use the same files you used.
Asset URLs can be a number of different **protocols**: HTTP, HTTPS, FTP, SSH,
and even **cloud storage** such as GCS and S3. You can also download assets from
a **Git repo** instead.

### Downloading from a URL or cloud storage

Under the hood, Weasel uses the
[`smart-open`](https://github.com/RaRe-Technologies/smart_open) library so you
can use any protocol it supports. Note that you may need to install extra
dependencies to use certain protocols.

> :bulb: **Example configuration**
>
> ```yaml title="project.yml"
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
| `extra`       | Optional flag determining whether this asset is downloaded only if `weasel assets` is run with `--extra`. `False` by default.                                                    |
| `url`         | The URL to download from, using the respective protocol.                                                                                                                         |
| `checksum`    | Optional checksum of the file. If provided, it will be used to verify that the file matches and downloads will be skipped if a local file with the same checksum already exists. |
| `description` | Optional asset description, used in [auto-generated docs](../cli.md#closed_book-document).                                                                                       |

### Downloading from a Git repo

If a `git` block is provided, the asset is downloaded from the given Git
repository. You can download from any repo that you have access to. Under the
hood, this uses Git's "sparse checkout" feature, so you're only downloading the
files you need and not the whole repo.

> :bulb: **Example configuration**
>
> ```yaml title="project.yml"
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
| `description` | Optional asset description, used in [auto-generated docs](../cli.md#closed_book-document).                                                                                                                                            |

### Working with private assets

> :bulb: **Example configuration**
>
> ```yaml title="project.yml"
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
directory themselves. The [`assets`](../cli.md#open_file_folder-assets) command
will alert you about missing files and mismatched checksums, so you can ensure
that others are running your project with the same data.

## Dependencies and outputs

Each command defined in the `project.yml` can optionally define a list of
dependencies and outputs. These are the files the command requires and creates.
For example, a command for training a spaCy pipeline may depend on a
[`config.cfg`](https://spacy.io/usage/training#config) and the training and evaluation data, and
it will export a directory `model-best`, which you can then re-use in other
commands.

> :bulb: **Example configuration**
>
> ```yaml title="project.yml"
> commands:
> - name: train
>     help: 'Train a spaCy pipeline using the specified corpus and config'
>     script:
>     - 'python -m spacy train ./configs/config.cfg -o training/ --paths.train ./corpus/training.spacy --paths.dev ./corpus/evaluation.spacy'
>     deps:
>     - 'configs/config.cfg'
>     - 'corpus/training.spacy'
>     - 'corpus/evaluation.spacy'
>     outputs:
>     - 'training/model-best'
> ```

> :boom: **Tip: Re-running vs. skipping**
>
> Under the hood, Weasel uses a `project.lock` lockfile that stores the details
> for each command, as well as its dependencies and outputs and their checksums.
> It's updated on each run. If any of this information changes, the command will
> be re-run. Otherwise, it will be skipped.

If you're running a command and it depends on files that are missing, Weasel will
show you an error. If a command defines dependencies and outputs that haven't
changed since the last run, the command will be skipped. This means that you're
only re-running commands if they need to be re-run. Commands can also set
`no_skip: true` if they should never be skipped – for example commands that run
tests. Commands without outputs are also never skipped. To force re-running a
command or workflow, even if nothing changed, you can set the `--force` flag.

Note that [`weasel`](../cli.md) doesn't compile any dependency
graphs based on the dependencies and outputs, and won't re-run previous steps
automatically. For instance, if you only run the command `train` that depends on
data created by `preprocess` and those files are missing, Weasel will show an
error – it won't just re-run `preprocess`. If you're looking for more advanced
data management, check out the [Data Version Control (DVC) integration](./integrations.md#data-version-control-dvc).
If you're planning on integrating your Weasel project with DVC, you can also use
`outputs_no_cache` instead of `outputs` to define outputs that won't be cached
or tracked.

## Files and directory structure

The `project.yml` can define a list of `directories` that should be created
within a project – for instance, `assets`, `training`, `corpus` and so on. Weasel
will make sure that these directories are always available, so your commands can
write to and read from them. Project directories will also include all files and
directories copied from the project template with
[`weasel clone`](../cli.md#clipboard-clone). Here's an example of a project
directory:

> :bulb: **Example configuration**
>
> ```yaml title="project.yml"
> directories:
>   - 'assets'
>   - 'configs'
>   - 'corpus'
>   - 'metas'
>   - 'metrics'
>   - 'notebooks'
>   - 'packages'
>   - 'scripts'
>   - 'training'
> ```
>
>``` title="Example directory structure"
>├── project.yml          # the project settings
>├── project.lock         # lockfile that tracks inputs/outputs
>├── assets/              # downloaded data assets
>├── configs/             # pipeline config.cfg files used for training
>├── corpus/              # output directory for training corpus
>├── metas/               # pipeline meta.json templates used for packaging
>├── metrics/             # output directory for evaluation metrics
>├── notebooks/           # directory for Jupyter notebooks
>├── packages/            # output directory for pipeline Python packages
>├── scripts/             # directory for scripts, e.g. referenced in commands
>├── training/            # output directory for trained pipelines
>└── ...                  # any other files, like a requirements.txt etc.
>```

If you don't want a project to create a directory, you can delete it and remove
its entry from the `project.yml` – just make sure it's not required by any of
the commands. [Custom templates](./custom-scripts.md) can use any directories they need –
the only file that's required for a project is the `project.yml`.
