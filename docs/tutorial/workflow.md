# Workflow

## 1. Clone a project template

!!! note "Cloning under the hood"

    To clone a project, spaCy calls into `git` and uses the "sparse checkout"
    feature to only clone the relevant directory or directories.

The [`weasel clone`](../cli.md#clone) command clones an existing
project template and copies the files to a local directory. You can then run the
project, e.g. to train a pipeline and edit the commands and scripts to build
fully custom workflows.

```bash
python -m weasel clone pipelines/tagger_parser_ud
```

By default, the project will be cloned into the current working directory. You
can specify an optional second argument to define the output directory. The
`--repo` option lets you define a custom repo to clone from if you don't want to
use the default [`projects`](https://github.com/explosion/projects) repo. You can
also use any private repo you have access to with Git.

## 2. Fetch the project assets

Assets are data files your project needs – for example, the training and
evaluation data or pretrained vectors and embeddings to initialize your model
with. Each project template comes with a `project.yml` that defines the assets
to download and where to put them. The [`weasel assets`](../cli.md#run)
will fetch the project assets for you.

???+ example "Example usage"

    ```yaml title="project.yml"
    assets:
    - dest: 'assets/training.spacy'
        url: 'https://example.com/data.spacy'
        checksum: '63373dd656daa1fd3043ce166a59474c'
    - dest: 'assets/development.spacy'
        git:
        repo: 'https://github.com/example/repo'
        branch: 'master'
        path: 'path/development.spacy'
        checksum: '5113dc04e03f079525edd8df3f4f39e3'
    ```

    Let Weasel fetch the assets:

    ```bash
    python -m weasel assets
    ```

Asset URLs can be a number of different protocols: HTTP, HTTPS, FTP, SSH, and
even cloud storage such as GCS and S3. You can also fetch assets using git, by
replacing the `url` string with a `git` block. spaCy will use Git's "sparse
checkout" feature to avoid downloading the whole repository.

Sometimes your project configuration may include large assets that you don't
necessarily want to download when you run `weasel assets`. That's why
assets can be marked as [`extra`](#data-assets-url) - by default, these assets
are not downloaded. If they should be, run `weasel assets --extra`.

## 3. Run a command

Commands consist of one or more steps and can be run with
[`weasel run`](../cli.md#run). The following will run the command
`preprocess` defined in the `project.yml`:

???+ example "Example usage"

    ```yaml title="project.yml"
    commands:
    - name: preprocess
        help: "Convert the input data to spaCy's format"
        script:
        - 'python -m spacy convert assets/train.conllu corpus/'
        - 'python -m spacy convert assets/eval.conllu corpus/'
        deps:
        - 'assets/train.conllu'
        - 'assets/eval.conllu'
        outputs:
        - 'corpus/train.spacy'
        - 'corpus/eval.spacy'
    ```

    Run the command:

    ```bash
    python -m weasel run preprocess
    ```

Commands can define their expected [dependencies and outputs](#deps-outputs)
using the `deps` (files the commands require) and `outputs` (files the commands
create) keys. This allows your project to track changes and determine whether a
command needs to be re-run. For instance, if your input data changes, you want
to re-run the `preprocess` command. But if nothing changed, this step can be
skipped. You can also set `--force` to force re-running a command, or `--dry` to
perform a "dry run" and see what would happen (without actually running the
script).

Since spaCy v3.4.2, `weasels run` checks your installed dependencies to
verify that your environment is properly set up and aligns with the project's
`requirements.txt`, if there is one. If missing or conflicting dependencies are
detected, a corresponding warning is displayed. If you'd like to disable the
dependency check, set `check_requirements: false` in your project's
`project.yml`.

## 4. Run a workflow

Workflows are series of commands that are run in order and often depend on each
other. For instance, to generate a spaCy pipeline package, you might start by
converting your data, then run [`spacy train`](https://spacy.io/api/cli#train) to train your
pipeline on the converted data and if that's successful, run
[`spacy package`](https://spacy.io/api/cli#package) to turn the best trained artifact into an
installable Python package. The following command runs the workflow named `all`
defined in the `project.yml`, and executes the commands it specifies, in order:

???+ example "Example usage"

    ```yaml title="project.yml"
    workflows:
    all:
        - preprocess
        - train
        - package
    ```

    ```bash
    python -m weasel run all
    ```

Using the expected [dependencies and outputs](./directory-and-assets.md#dependencies-and-outputs) defined in the
commands, spaCy can determine whether to re-run a command (if its inputs or
outputs have changed) or whether to skip it. If you're looking to implement more
advanced data pipelines and track your changes in Git, check out the
[Data Version Control (DVC) integration](./integrations.md#data-version-control-dvc). The
[`weasel dvc`](../cli.md#dvc) command generates a DVC config file
from a workflow defined in your `project.yml` so you can manage your spaCy
project as a DVC repo.

## 5. Optional: Push to remote storage

After training a pipeline, you can optionally use the
[`weasel push`](../cli.md#push) command to upload your outputs to
a remote storage, using protocols like [S3](https://aws.amazon.com/s3/),
[Google Cloud Storage](https://cloud.google.com/storage) or SSH. This can help
you **export** your pipeline packages, **share** work with your team, or **cache
results** to avoid repeating work.

???+ example "Example usage"

    ```yaml title="project.yml"
    remotes:
      default: 's3://my-spacy-bucket'
      local: '/mnt/scratch/cache'
    ```

    Push to remote:

    ```bash
    python -m weasel push
    ```

The `remotes` section in your `project.yml` lets you assign names to the
different storages. To download state from a remote storage, you can use the
[`weasel pull`](../cli.md#pull) command. For more details, see the
docs on [remote storage](./remote-storage.md).
