# Command Line Interface

The `weasel` CLI includes subcommands for working with
Weasel projects, end-to-end workflows for building and
deploying custom spaCy pipelines.

## :clipboard: clone

Clone a project template from a Git repository. Calls into `git` under the hood
and can use the sparse checkout feature if available, so you're only downloading
what you need. By default, spaCy's
[project templates repo](https://github.com/explosion/projects) is used, but you
can provide any other repo (public or private) that you have access to using the
`--repo` option.

```bash
python -m weasel clone [name] [dest] [--repo] [--branch] [--sparse]
```

> :bulb: **Example usage**
>
> ```bash
> $ python -m weasel clone pipelines/ner_wikiner
> ```

| Name             | Description                                                                                                                                               |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`           | The name of the template to clone, relative to the repo. Can be a top-level directory or a subdirectory like `dir/template`. ~~str (positional)~~         |
| `dest`           | Where to clone the project. Defaults to current working directory. ~~Path (positional)~~                                                                  |
| `--repo`, `-r`   | The repository to clone from. Can be any public or private Git repo you have access to. ~~str (option)~~                                                  |
| `--branch`, `-b` | The branch to clone from. Defaults to `master`. ~~str (option)~~                                                                                          |
| `--sparse`, `-S` | Enable [sparse checkout](https://git-scm.com/docs/git-sparse-checkout) to only check out and download what's needed. Requires Git v22.2+. ~~bool (flag)~~ |
| `--help`, `-h`   | Show help message and available arguments. ~~bool (flag)~~                                                                                                |
| **CREATES**      | The cloned [project directory](tutorial/directory-and-assets.md).                                                                                         |

## :open_file_folder: assets

Fetch project assets like datasets and pretrained weights. Assets are defined in
the `assets` section of the [`project.yml`](tutorial/directory-and-assets.md#project-yml). If a
`checksum` is provided, the file is only downloaded if no local file with the
same checksum exists and spaCy will show an error if the checksum of the
downloaded file doesn't match. If assets don't specify a `url` they're
considered "private" and you have to take care of putting them into the
destination directory yourself. If a local path is provided, the asset is copied
into the current project.

```bash
python -m weasel assets [project_dir]
```

| Name                                           | Description                                                                                                                                               |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project_dir`                                  | Path to project directory. Defaults to current working directory. ~~Path (positional)~~                                                                   |
| `--extra`, `-e` <Tag variant="new">3.3.1</Tag> | Download assets marked as "extra". Default false. ~~bool (flag)~~                                                                                         |
| `--sparse`, `-S`                               | Enable [sparse checkout](https://git-scm.com/docs/git-sparse-checkout) to only check out and download what's needed. Requires Git v22.2+. ~~bool (flag)~~ |
| `--help`, `-h`                                 | Show help message and available arguments. ~~bool (flag)~~                                                                                                |
| **CREATES**                                    | Downloaded or copied assets defined in the `project.yml`.                                                                                                 |

## :rocket: run

Run a named command or workflow defined in the
[`project.yml`](tutorial/directory-and-assets.md#project-yml). If a workflow name is specified,
all commands in the workflow are run, in order. If commands define
[dependencies or outputs](tutorial/directory-and-assets.md#dependencies-and-outputs), they will only be
re-run if state has changed. For example, if the input dataset changes, a
preprocessing command that depends on those files will be re-run.

```bash
python -m weasel run [subcommand] [project_dir] [--force] [--dry]
```

| Name            | Description                                                                             |
| --------------- | --------------------------------------------------------------------------------------- |
| `subcommand`    | Name of the command or workflow to run. ~~str (positional)~~                            |
| `project_dir`   | Path to project directory. Defaults to current working directory. ~~Path (positional)~~ |
| `--force`, `-F` | Force re-running steps, even if nothing changed. ~~bool (flag)~~                        |
| `--dry`, `-D`   | Perform a dry run and don't execute scripts. ~~bool (flag)~~                            |
| `--help`, `-h`  | Show help message and available arguments. ~~bool (flag)~~                              |
| **EXECUTES**    | The command defined in the `project.yml`.                                               |

## :arrow_up: push

Upload all available files or directories listed as in the `outputs` section of
commands to a remote storage. Outputs are archived and compressed prior to
upload, and addressed in the remote storage using the output's relative path
(URL encoded), a hash of its command string and dependencies, and a hash of its
file contents. This means `push` should **never overwrite** a file in your
remote. If all the hashes match, the contents are the same and nothing happens.
If the contents are different, the new version of the file is uploaded. Deleting
obsolete files is left up to you.

Remotes can be defined in the `remotes` section of the
[`project.yml`](tutorial/directory-and-assets.md#project-yml). Under the hood, spaCy uses
[`Pathy`](https://github.com/justindujardin/pathy) to communicate with the
remote storages, so you can use any protocol that `Pathy` supports, including
[S3](https://aws.amazon.com/s3/),
[Google Cloud Storage](https://cloud.google.com/storage), and the local
filesystem, although you may need to install extra dependencies to use certain
protocols.

```bash
python -m weasel push [remote] [project_dir]
```

> :bulb: **Example**
>
> ```bash
> $ python -m weasel push my_bucket
> ```
>
> ```yaml title="project.yml"
> remotes:
>   my_bucket: 's3://my-weasel-bucket'
> ```

| Name           | Description                                                                             |
| -------------- | --------------------------------------------------------------------------------------- |
| `remote`       | The name of the remote to upload to. Defaults to `"default"`. ~~str (positional)~~      |
| `project_dir`  | Path to project directory. Defaults to current working directory. ~~Path (positional)~~ |
| `--help`, `-h` | Show help message and available arguments. ~~bool (flag)~~                              |
| **UPLOADS**    | All project outputs that exist and are not already stored in the remote.                |

## :arrow_down: pull

Download all files or directories listed as `outputs` for commands, unless they
are already present locally. When searching for files in the remote, `pull`
won't just look at the output path, but will also consider the **command
string** and the **hashes of the dependencies**. For instance, let's say you've
previously pushed a checkpoint to the remote, but now you've changed some
hyper-parameters. Because you've changed the inputs to the command, if you run
`pull`, you won't retrieve the stale result. If you train your pipeline and push
the outputs to the remote, the outputs will be saved alongside the prior
outputs, so if you change the config back, you'll be able to fetch back the
result.

Remotes can be defined in the `remotes` section of the
[`project.yml`](tutorial/directory-and-assets.md#project-yml). Under the hood, spaCy uses
[`Pathy`](https://github.com/justindujardin/pathy) to communicate with the
remote storages, so you can use any protocol that `Pathy` supports, including
[S3](https://aws.amazon.com/s3/),
[Google Cloud Storage](https://cloud.google.com/storage), and the local
filesystem, although you may need to install extra dependencies to use certain
protocols.

```bash
python -m weasel pull [remote] [project_dir]
```

> :bulb: **Example**
>
> ```bash
> $ python -m weasel pull my_bucket
> ```
>
> ```yaml title="project.yml"
> remotes:
>   my_bucket: 's3://my-weasel-bucket'
> ```

| Name           | Description                                                                             |
| -------------- | --------------------------------------------------------------------------------------- |
| `remote`       | The name of the remote to download from. Defaults to `"default"`. ~~str (positional)~~  |
| `project_dir`  | Path to project directory. Defaults to current working directory. ~~Path (positional)~~ |
| `--help`, `-h` | Show help message and available arguments. ~~bool (flag)~~                              |
| **DOWNLOADS**  | All project outputs that do not exist locally and can be found in the remote.           |

## :closed_book: document

Auto-generate a pretty Markdown-formatted `README` for your project, based on
its [`project.yml`](tutorial/directory-and-assets.md#project-yml). Will create sections that
document the available commands, workflows and assets. The auto-generated
content will be placed between two hidden markers, so you can add your own
custom content before or after the auto-generated documentation. When you re-run
the `project document` command, only the auto-generated part is replaced.

```bash
python -m weasel document [project_dir] [--output] [--no-emoji]
```

> :bulb: **Example usage**
>
> ```bash
> $ python -m weasel document --output README.md
> ```
>
> For more examples, see the templates in our
> [`projects`](https://github.com/explosion/projects) repo.

| Name                | Description                                                                                                                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project_dir`       | Path to project directory. Defaults to current working directory. ~~Path (positional)~~                                                                                                                 |
| `--output`, `-o`    | Path to output file or `-` for stdout (default). If a file is specified and it already exists and contains auto-generated docs, only the auto-generated docs section is replaced. ~~Path (positional)~~ |
| `--no-emoji`, `-NE` | Don't use emoji in the titles. ~~bool (flag)~~                                                                                                                                                          |
| **CREATES**         | The Markdown-formatted project documentation.                                                                                                                                                           |

## :repeat: dvc

Auto-generate [Data Version Control](https://dvc.org) (DVC) config file. Calls
[`dvc run`](https://dvc.org/doc/command-reference/run) with `--no-exec` under
the hood to generate the `dvc.yaml`. A DVC project can only define one pipeline,
so you need to specify one workflow defined in the
[`project.yml`](tutorial/directory-and-assets.md#project-yml). If no workflow is specified, the
first defined workflow is used. The DVC config will only be updated if the
`project.yml` changed. For details, see the
[DVC integration](tutorial/integrations.md#data-version-control-dvc) docs.

> **Warning**
>
> This command requires DVC to be installed and initialized in the project
> directory, e.g. via [`dvc init`](https://dvc.org/doc/command-reference/init).
> You'll also need to add the assets you want to track with
> [`dvc add`](https://dvc.org/doc/command-reference/add).

```bash
python -m weasel dvc [project_dir] [workflow] [--force] [--verbose] [--quiet]
```

> :bulb: **Example**
>
> ```bash
> $ git init
> $ dvc init
> $ python -m weasel dvc all
> ```

| Name              | Description                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------------- |
| `project_dir`     | Path to project directory. Defaults to current working directory. ~~Path (positional)~~                       |
| `workflow`        | Name of workflow defined in `project.yml`. Defaults to first workflow if not set. ~~Optional[str] \(option)~~ |
| `--force`, `-F`   | Force-updating config file. ~~bool (flag)~~                                                                   |
| `--verbose`, `-V` | Print more output generated by DVC. ~~bool (flag)~~                                                           |
| `--quiet`, `-q`   | Print no output generated by DVC. ~~bool (flag)~~                                                             |
| `--help`, `-h`    | Show help message and available arguments. ~~bool (flag)~~                                                    |
| **CREATES**       | A `dvc.yaml` file in the project directory, based on the steps defined in the given workflow.                 |
