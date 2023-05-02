# Overview

Weasel lets you manage and share **end-to-end workflows** for
different **use cases and domains**, and orchestrate training, packaging and
serving your custom pipelines. You can start off by cloning a pre-defined
project template, adjust it to fit your needs, load in your data, train a
pipeline, export it as a Python package, upload your outputs to a remote storage
and share your results with your team. Weasel can be used via the
[`weasel`](../cli.md) command and we provide templates in our
[`projects`](https://github.com/explosion/projects) repo.

![Illustration of project workflow and commands](assets/images/projects.svg)

!!! example "Get started with a project template: `pipelines/tagger_parser_ud`"

    The easiest way to get started is to clone a project template and run it – for
    example, this end-to-end template that lets you train a spaCy **part-of-speech
    tagger** and **dependency parser** on a Universal Dependencies treebank.

    ```shell
    python -m weasel clone pipelines/tagger_parser_ud
    ```

<!-- Weasel makes it easy to integrate with many other **awesome tools** in
the data science and machine learning ecosystem to track and manage your data
and experiments, iterate on demos and prototypes and ship your models into
production.

<Grid narrow cols={3}>
  <Integration title="DVC" logo="dvc" url="#dvc">
    Manage and version your data
  </Integration>
  <Integration title="Prodigy" logo="prodigy" url="#prodigy">
    Create labelled training data
  </Integration>
  <Integration title="Streamlit" logo="streamlit" url="#streamlit">
    Visualize and demo your pipelines
  </Integration>
  <Integration title="FastAPI" logo="fastapi" url="#fastapi">
    Serve your models and host APIs
  </Integration>
  <Integration title="Ray" logo="ray" url="#ray">
    Distributed and parallel training
  </Integration>
  <Integration title="Weights &amp; Biases" logo="wandb" url="#wandb">
    Track your experiments and results
  </Integration>
  <Integration
    title="Hugging Face Hub"
    logo="huggingface_hub"
    url="#huggingface_hub"
  >
    Upload your pipelines to the Hugging Face Hub
  </Integration>
</Grid> -->

!!! project "Project templates"

    Our [`projects`](https://github.com/explosion/projects) repo includes various
    project templates for different NLP tasks, models, workflows and integrations
    that you can clone and run. The easiest way to get started is to pick a
    template, clone it and start modifying it!
