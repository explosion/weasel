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

<Infobox title="Important note on privacy" variant="warning">

DVC enables usage analytics by default, so if you're working in a
privacy-sensitive environment, make sure to
[**opt-out manually**](https://dvc.org/doc/user-guide/analytics#opting-out).

</Infobox>

The [`spacy project dvc`](/api/cli#project-dvc) command creates a `dvc.yaml`
config file based on a workflow defined in your `project.yml`. Whenever you
update your project, you can re-run the command to update your DVC config. You
can then manage your spaCy project like any other DVC project, run
[`dvc add`](https://dvc.org/doc/command-reference/add) to add and track assets
and [`dvc repro`](https://dvc.org/doc/command-reference/repro) to reproduce the
workflow or individual commands.

```bash
python -m spacy project dvc [project_dir] [workflow_name]
```

<Infobox title="Important note for multiple workflows" variant="warning">

DVC currently expects a single workflow per project, so when creating the config
with [`spacy project dvc`](/api/cli#project-dvc), you need to specify the name
of a workflow defined in your `project.yml`. You can still use multiple
workflows, but only one can be tracked by DVC.

</Infobox>

{/*{ TODO: <Project id="integrations/dvc"></Project>}*/}

---

{<H3 id="prodigy">Prodigy

<IntegrationLogo name="prodigy" width={100} height="auto" align="right" />
</H3>}

[Prodigy](https://prodi.gy) is a modern annotation tool for creating training
data for machine learning models, developed by us. It integrates with spaCy
out-of-the-box and provides many different
[annotation recipes](https://prodi.gy/docs/recipes) for a variety of NLP tasks,
with and without a model in the loop. If Prodigy is installed in your project,
you can start the annotation server from your `project.yml` for a tight feedback
loop between data development and training.

<Infobox variant="warning">

This integration requires [Prodigy v1.11](https://prodi.gy/docs/changelog#v1.11)
or higher. If you're using an older version of Prodigy, you can still use your
annotations in spaCy v3 by exporting your data with
[`data-to-spacy`](https://prodi.gy/docs/recipes#data-to-spacy) and running
[`spacy convert`](/api/cli#convert) to convert it to the binary format.

</Infobox>

The following example shows a workflow for merging and exporting NER annotations
collected with Prodigy and training a spaCy pipeline:

> #### Example usage
>
> ```bash
> $ python -m spacy project run all
> ```

{/*prettier-ignore*/}

```yaml {title="project.yml"}
vars:
  prodigy:
    train_dataset: "fashion_brands_training"
    eval_dataset: "fashion_brands_eval"

workflows:
  all:
    - data-to-spacy
    - train_spacy

commands:
  - name: "data-to-spacy"
    help: "Merge your annotations and create data in spaCy's binary format"
    script:
      - "python -m prodigy data-to-spacy corpus/ --ner ${vars.prodigy.train_dataset},eval:${vars.prodigy.eval_dataset}"
    outputs:
      - "corpus/train.spacy"
      - "corpus/dev.spacy"
  - name: "train_spacy"
    help: "Train a named entity recognition model with spaCy"
    script:
      - "python -m spacy train configs/config.cfg --output training/ --paths.train corpus/train.spacy --paths.dev corpus/dev.spacy"
    deps:
      - "corpus/train.spacy"
      - "corpus/dev.spacy"
    outputs:
      - "training/model-best"
```

> #### Example train curve output
>
> <Image
> src="/images/prodigy_train_curve.jpg"
> href="https://prodi.gy/docs/recipes#train-curve"
> alt="Screenshot of train curve terminal output"
> />

The [`train-curve`](https://prodi.gy/docs/recipes#train-curve) recipe is another
cool workflow you can include in your project. It will run the training with
different portions of the data, e.g. 25%, 50%, 75% and 100%. As a rule of thumb,
if accuracy increases in the last segment, this could indicate that collecting
more annotations of the same type might improve the model further.

{/*prettier-ignore*/}

```yaml {title="project.yml (excerpt)"}
- name: "train_curve"
    help: "Train the model with Prodigy by using different portions of training examples to evaluate if more annotations can potentially improve the performance"
    script:
      - "python -m prodigy train-curve --ner ${vars.prodigy.train_dataset},eval:${vars.prodigy.eval_dataset} --config configs/${vars.config} --show-plot"
```

You can use the same approach for various types of projects and annotation
workflows, including
[named entity recognition](https://prodi.gy/docs/named-entity-recognition),
[span categorization](https://prodi.gy/docs/span-categorization),
[text classification](https://prodi.gy/docs/text-classification),
[dependency parsing](https://prodi.gy/docs/dependencies-relations),
[part-of-speech tagging](https://prodi.gy/docs/recipes#pos) or fully
[custom recipes](https://prodi.gy/docs/custom-recipes). You can also use spaCy
project templates to quickly start the annotation server to collect more
annotations and add them to your Prodigy dataset.

<Project id="integrations/prodigy">

Get started with spaCy and Prodigy using our project template. It includes
commands to create a merged training corpus from your Prodigy annotations,
training and packaging a spaCy pipeline and analyzing if more annotations may
improve performance.

</Project>

---

{<H3 id="streamlit">Streamlit

<IntegrationLogo name="streamlit" width={150} height="auto" align="right" />
</H3>}

[Streamlit](https://streamlit.io) is a Python framework for building interactive
data apps. The [`spacy-streamlit`](https://github.com/explosion/spacy-streamlit)
package helps you integrate spaCy visualizations into your Streamlit apps and
quickly spin up demos to explore your pipelines interactively. It includes a
full embedded visualizer, as well as individual components.

{/*TODO: update once version is stable*/}

> #### Installation
>
> ```bash
> $ pip install spacy-streamlit --pre
> ```

![Screenshot of the spacy-streamlit package in Streamlit](/images/spacy-streamlit.png)

Using [`spacy-streamlit`](https://github.com/explosion/spacy-streamlit), your
projects can easily define their own scripts that spin up an interactive
visualizer, using the latest pipeline you trained, or a selection of pipelines
so you can compare their results.

<Project id="integrations/streamlit">

Get started with spaCy and Streamlit using our project template. It includes a
script to spin up a custom visualizer and commands you can adjust to showcase
and explore your own custom trained pipelines.

</Project>

> #### Example usage
>
> ```bash
> $ python -m spacy project run visualize
> ```

{/*prettier-ignore*/}

```yaml {title="project.yml"}
commands:
  - name: visualize
    help: "Visualize the pipeline's output interactively using Streamlit"
    script:
      - 'streamlit run ./scripts/visualize.py ./training/model-best "I like Adidas shoes."'
    deps:
      - "training/model-best"
```

The following script is called from the `project.yml` and takes two positional
command-line argument: a comma-separated list of paths or packages to load the
pipelines from and an example text to use as the default text.

```python
https://github.com/explosion/projects/blob/v3/integrations/streamlit/scripts/visualize.py
```

---

{<H3 id="fastapi">FastAPI

<IntegrationLogo name="fastapi" width={100} height="auto" align="right" />
</H3>}

[FastAPI](https://fastapi.tiangolo.com/) is a modern high-performance framework
for building REST APIs with Python, based on Python
[type hints](https://fastapi.tiangolo.com/python-types/). It's become a popular
library for serving machine learning models and you can use it in your spaCy
projects to quickly serve up a trained pipeline and make it available behind a
REST API.

<Project id="integrations/fastapi">

Get started with spaCy and FastAPI using our project template. It includes a
simple REST API for processing batches of text, and usage examples for how to
query your API from Python and JavaScript (Vanilla JS and React).

</Project>

> #### Example usage
>
> ```bash
> $ python -m spacy project run serve
> ```

{/*prettier-ignore*/}

```yaml {title="project.yml"}
  - name: "serve"
    help: "Serve the models via a FastAPI REST API using the given host and port"
    script:
      - "uvicorn scripts.main:app --reload --host 127.0.0.1 --port 5000"
    deps:
      - "scripts/main.py"
    no_skip: true
```

The script included in the template shows a simple REST API with a `POST`
endpoint that accepts batches of texts and returns batches of predictions, e.g.
named entities found in the documents. Type hints and
[`pydantic`](https://github.com/samuelcolvin/pydantic) are used to define the
expected data types.

```python
https://github.com/explosion/projects/blob/v3/integrations/fastapi/scripts/main.py
```

---

{<H3 id="wandb">Weights & Biases

<IntegrationLogo name="wandb" width={175} height="auto" align="right" />
</H3>}

[Weights & Biases](https://www.wandb.com/) is a popular platform for experiment
tracking. spaCy integrates with it out-of-the-box via the
[`WandbLogger`](https://github.com/explosion/spacy-loggers#wandblogger), which
you can add as the `[training.logger]` block of your training
[config](/usage/training#config). The results of each step are then logged in
your project, together with the full **training config**. This means that
*every* hyperparameter, registered function name and argument will be tracked
and you'll be able to see the impact it has on your results.

> #### Example config
>
> ```ini
> [training.logger]
> @loggers = "spacy.WandbLogger.v3"
> project_name = "monitor_spacy_training"
> remove_config_values = ["paths.train", "paths.dev", "corpora.train.path", "corpora.dev.path"]
> log_dataset_dir = "corpus"
> model_log_interval = 1000
> ```

![Screenshot: Visualized training results](/images/wandb1.jpg)

![Screenshot: Parameter importance using config values](/images/wandb2.jpg 'Parameter importance using config values')

<Project id="integrations/wandb">

Get started with tracking your spaCy training runs in Weights & Biases using our
project template. It trains on the IMDB Movie Review Dataset and includes a
simple config with the built-in `WandbLogger`, as well as a custom example of
creating variants of the config for a simple hyperparameter grid search and
logging the results.

</Project>

---

{<H3 id="huggingface_hub">Hugging Face Hub

<IntegrationLogo name="huggingface_hub" width={175} height="auto" align="right" />
</H3>}

The [Hugging Face Hub](https://huggingface.co/) lets you upload models and share
them with others. It hosts models as Git-based repositories which are storage
spaces that can contain all your files. It support versioning, branches and
custom metadata out-of-the-box, and provides browser-based visualizers for
exploring your models interactively, as well as an API for production use. The
[`spacy-huggingface-hub`](https://github.com/explosion/spacy-huggingface-hub)
package automatically adds the `huggingface-hub` command to your `spacy` CLI if
it's installed.

> #### Installation
>
> ```bash
> $ pip install spacy-huggingface-hub
> # Check that the CLI is registered
> $ python -m spacy huggingface-hub --help
> ```

You can then upload any pipeline packaged with
[`spacy package`](/api/cli#package). Make sure to set `--build wheel` to output
a binary `.whl` file. The uploader will read all metadata from the pipeline
package, including the auto-generated pretty `README.md` and the model details
available in the `meta.json`. For examples, check out the
[spaCy pipelines](https://huggingface.co/spacy) we've uploaded.

```bash
huggingface-cli login
python -m spacy package ./en_ner_fashion ./output --build wheel
cd ./output/en_ner_fashion-0.0.0/dist
python -m spacy huggingface-hub push en_ner_fashion-0.0.0-py3-none-any.whl
```

After uploading, you will see the live URL of your pipeline packages, as well as
the direct URL to the model wheel you can install via `pip install`. You'll also
be able to test your pipeline interactively from your browser:

![Screenshot: interactive NER visualizer](/images/huggingface_hub.jpg)

In your `project.yml`, you can add a command that uploads your trained and
packaged pipeline to the hub. You can either run this as a manual step, or
automatically as part of a workflow. Make sure to set `--build wheel` when
running `spacy package` to build a wheel file for your pipeline package.

{/*prettier-ignore*/}

```yaml {title="project.yml"}
- name: "push_to_hub"
  help: "Upload the trained model to the Hugging Face Hub"
  script:
    - "python -m spacy huggingface-hub push packages/en_${vars.name}-${vars.version}/dist/en_${vars.name}-${vars.version}-py3-none-any.whl"
  deps:
    - "packages/en_${vars.name}-${vars.version}/dist/en_${vars.name}-${vars.version}-py3-none-any.whl"
```

<Project id="integrations/huggingface_hub">

Get started with uploading your models to the Hugging Face hub using our project
template. It trains a simple pipeline, packages it and uploads it if the
packaged model has changed. This makes it easy to deploy your models end-to-end.

</Project>
