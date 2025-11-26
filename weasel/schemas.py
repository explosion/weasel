from collections import defaultdict
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import VERSION as PYDANTIC_VERSION
from pydantic import BaseModel, Field, StrictStr, ValidationError
from wasabi import msg

IS_PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")


def validate(schema: Type[BaseModel], obj: Dict[str, Any]) -> List[str]:
    """Validate data against a given pydantic schema.

    obj (Dict[str, Any]): JSON-serializable data to validate.
    schema (pydantic.BaseModel): The schema to validate against.
    RETURNS (List[str]): A list of error messages, if available.
    """
    try:
        schema(**obj)
        return []
    except ValidationError as e:
        errors = e.errors()
        data = defaultdict(list)
        for error in errors:
            err_loc = " -> ".join([str(p) for p in error.get("loc", [])])
            data[err_loc].append(error.get("msg"))
        return [f"[{loc}] {', '.join(msg)}" for loc, msg in data.items()]  # type: ignore[arg-type]


# Project config Schema


class ProjectConfigAssetGitItem(BaseModel):
    # fmt: off
    repo: StrictStr = Field(..., title="URL of Git repo to download from")
    path: StrictStr = Field(..., title="File path or sub-directory to download (used for sparse checkout)")
    branch: StrictStr = Field("master", title="Branch to clone from")
    # fmt: on


CHECKSUM_REGEX = r"([a-fA-F\d]{32})"
ChecksumField = (
    Field(None, title="MD5 hash of file", pattern=CHECKSUM_REGEX)
    if IS_PYDANTIC_V2
    else Field(None, title="MD5 hash of file", regex=CHECKSUM_REGEX)
)


class ProjectConfigAssetURL(BaseModel):
    # fmt: off
    dest: StrictStr = Field(..., title="Destination of downloaded asset")
    url: Optional[StrictStr] = Field(None, title="URL of asset")
    checksum: Optional[str] = ChecksumField
    description: StrictStr = Field("", title="Description of asset")
    # fmt: on


class ProjectConfigAssetGit(BaseModel):
    # fmt: off
    git: ProjectConfigAssetGitItem = Field(..., title="Git repo information")
    checksum: Optional[str] = ChecksumField
    description: Optional[StrictStr] = Field(None, title="Description of asset")
    # fmt: on


class ProjectConfigCommandBase(BaseModel):
    # fmt: off
    name: StrictStr = Field(..., title="Name of command")
    help: Optional[StrictStr] = Field(None, title="Command description")
    script: List[StrictStr] = Field([], title="List of CLI commands to run, in order")
    deps: List[StrictStr] = Field([], title="File dependencies required by this command")
    outputs: List[StrictStr] = Field([], title="Outputs produced by this command")
    outputs_no_cache: List[StrictStr] = Field([], title="Outputs not tracked by DVC (DVC only)")
    no_skip: bool = Field(False, title="Never skip this command, even if nothing changed")
    # fmt: on


PROJECT_CONFIG_COMMAND_TITLE = "A single named command specified in a project config"

if IS_PYDANTIC_V2:

    class ProjectConfigCommand(ProjectConfigCommandBase):
        model_config = {
            "title": PROJECT_CONFIG_COMMAND_TITLE,
            "extra": "forbid",
        }

else:

    class ProjectConfigCommand(ProjectConfigCommandBase):  # type: ignore[no-redef]
        class Config:
            title = PROJECT_CONFIG_COMMAND_TITLE
            extra = "forbid"


def check_legacy_keys(obj: Dict[str, Any]) -> Dict[str, Any]:
    if "spacy_version" in obj:
        msg.warn(
            "Your project configuration file includes a `spacy_version` key, "
            "which is now deprecated. Weasel will not validate your version of spaCy.",
        )
    if "check_requirements" in obj:
        msg.warn(
            "Your project configuration file includes a `check_requirements` key, "
            "which is now deprecated. Weasel will not validate your requirements.",
        )
    return obj


class ProjectConfigSchemaBase(BaseModel):
    # fmt: off
    vars: Dict[StrictStr, Any] = Field({}, title="Optional variables to substitute in commands")
    env: Dict[StrictStr, Any] = Field({}, title="Optional variable names to substitute in commands, mapped to environment variable names")
    assets: List[Union[ProjectConfigAssetURL, ProjectConfigAssetGit]] = Field([], title="Data assets")
    workflows: Dict[StrictStr, List[StrictStr]] = Field({}, title="Named workflows, mapped to list of project commands to run in order")
    commands: List[ProjectConfigCommand] = Field([], title="Project command shortucts")
    title: Optional[str] = Field(None, title="Project title")
    # fmt: on


PROJECT_CONFIG_TITLE = "Schema for project configuration file"

if IS_PYDANTIC_V2:
    from pydantic import model_validator

    class ProjectConfigSchema(ProjectConfigSchemaBase):
        model_config = {"title": PROJECT_CONFIG_TITLE}

        @model_validator(mode="before")
        @classmethod
        def check_legacy_keys(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
            return check_legacy_keys(obj)

else:
    from pydantic import root_validator

    class ProjectConfigSchema(ProjectConfigSchemaBase):  # type: ignore[no-redef]
        class Config:
            title = PROJECT_CONFIG_TITLE

        @root_validator(pre=True)
        def check_legacy_keys(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
            return check_legacy_keys(obj)
