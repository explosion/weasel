# Remote Storage

You can persist your project outputs to a remote storage using the
[`push`](../cli.md#push) command. This can help you **export**
your pipeline packages, **share** work with your team, or **cache results** to
avoid repeating work. The [`pull`](../cli.md#pull) command will
download any outputs that are in the remote storage and aren't available
locally.

You can list one or more remotes in the `remotes` section of your
[`project.yml`](./directory-and-assets.md#projectyml) by mapping a string name to the URL of the
storage. Under the hood, Weasel uses
[`Pathy`](https://github.com/justindujardin/pathy) to communicate with the
remote storages, so you can use any protocol that `Pathy` supports, including
[S3](https://aws.amazon.com/s3/),
[Google Cloud Storage](https://cloud.google.com/storage), and the local
filesystem, although you may need to install extra dependencies to use certain
protocols.

> :bulb: **Example using remote storage**
>
> ```bash
> $ python -m weasel pull local
> ```
>
> ```yaml title="project.yml"
> remotes:
> default: 's3://my-weasel-bucket'
> local: '/mnt/scratch/cache'
> ```

> :information_source: **How it works**
>
> Inside the remote storage, Weasel uses a clever **directory structure** to avoid
> overwriting files. The top level of the directory structure is a URL-encoded
> version of the output's path. Within this directory are subdirectories named
> according to a hash of the command string and the command's dependencies.
> Finally, within those directories are files, named according to an MD5 hash of
> their contents.
>
> ```
> └── urlencoded_file_path            # Path of original file
>     ├── some_command_hash           # Hash of command you ran
>     │   ├── some_content_hash       # Hash of file content
>     │   └── another_content_hash
>     └── another_command_hash
>         └── third_content_hash
> ```

For instance, let's say you had the following spaCy command in your `project.yml`:

```yaml title="project.yml"
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

After you finish training, you run [`push`](../cli.md#push) to
make sure the `training/model-best` output is saved to remote storage. Weasel
will then construct a hash from your command script and the listed dependencies,
`corpus/train`, `corpus/dev` and `config.cfg`, in order to identify the
execution context of your output. It would then compute an MD5 hash of the
`training/model-best` directory, and use those three pieces of information to
construct the storage URL.

```bash
python -m weasel run train
python -m weasel push
```

``` title="Overview of the S3 bucket"
└── s3://my-weasel-bucket/training%2Fmodel-best
    └── 1d8cb33a06cc345ad3761c6050934a1b
        └── d8e20c3537a084c5c10d95899fe0b1ff
```

If you change the command or one of its dependencies (for instance, by editing
the [`config.cfg`](/usage/training#config) file to tune the hyperparameters), a
different creation hash will be calculated, so when you use
[`push`](../cli.md#push) you won't be overwriting your previous
file. The system even supports multiple outputs for the same file and the same
context, which can happen if your training process is not deterministic, or if
you have dependencies that aren't represented in the command.

In summary, the `weasel` remote storages are designed
to make a particular set of trade-offs. Priority is placed on **convenience**,
**correctness** and **avoiding data loss**. You can use
[`push`](../cli.md#push) freely, as you'll never overwrite remote
state, and you don't have to come up with names or version numbers. However,
it's up to you to manage the size of your remote storage, and to remove files
that are no longer relevant to you.
