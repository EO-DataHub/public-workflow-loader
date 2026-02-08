# UK EO Data Hub Platform: Default Workflow Loader

This repository provides a command line application that can deploy any workflows in a given directory to the Workflow Runner on the EO DataHub Platform. It takes as inputs:
- The name of the workspace in which to deploy the workflows
- A directory containing any CWL files that are to be deployed to the workspace
- A directory containing templates to be used when generating access policy files
- An **optional** prefix parameter specifying the S3 bucket prefix for the access policies.

You can invoke the app as follows:
```
uv run python -m public_workflow_loader <workspace> <workflows-dir> <templates-dir> -p <prefix>
```

You also need to provide some environment variables for the Workflow Runner API, `WORKFLOW_RUNNER_API_URL`, and a Workspace-scoped API token, `WORKSPACE_API_TOKEN`, to be used in authenticated requests. This token needs to be scoped to the provided <workspace> command line input. To set these environment variables, an example .env file is provided, `sample.env`, please copy this and update it with your configuration values then load these environment variables:
```
set -a # allows us to export variables from the file
source .env # load environment variables into your local environment
```

You can confirm this worked by echoing the now set environment variables:
```
echo $WORKFLOW_RUNNER_API_URL
```

This application also uploads workflow access policies to S3 using boto3, so suitable AWS credentials need to be provided via environment variables.

This repository also includes a Dockerfile to build an image for this application which can then be run as a container wherever needed.

It is suggested you deploy this image and mount a volume into it, defining your CWL files, ensuring your specify the mount path of this volume in your command line input <workflows-dir>.

# Development of this component

## Getting started

### Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

### Install via makefile

```commandline
make setup
```

This will install all dependencies using `uv sync` and set up `pre-commit` hooks.

It's safe and fast to run `make setup` repeatedly as it will only update things if
they have changed.

After `make setup` you can run `make pre-commit` to run pre-commit checks on staged changes and
`make pre-commit-all` to run them on all files. This replicates the linter checks that
run from GitHub actions.

## Building and testing

This component uses `pytest` tests and `ruff` for linting and formatting, and `pyright` for type checking.

A number of `make` targets are defined:
* `make test`: run tests continuously (watch mode)
* `make testonce`: run tests once
* `make check`: run linting, formatting check, type checking, and pyproject validation
* `make format`: auto-fix lint issues and format code
* `make dockerbuild`: build a `latest` Docker image (use `make dockerbuild VERSION=1.2.3` for a release image)
* `make dockerpush`: push a `latest` Docker image (again, you can add `VERSION=1.2.3`) - normally this should be done
  only via the build system and its GitHub actions.

## Managing requirements

Runtime dependencies are specified in `pyproject.toml` under `[project.dependencies]`, and development
dependencies under `[dependency-groups]`. After changing them:

* Run `uv sync` to update the lockfile and install dependencies.
* Test your changes.
* Commit `pyproject.toml` and `uv.lock`.

## Releasing

Ensure that `make check` and `make testonce` work correctly and produce no errors before
continuing.

Releases tagged `latest` and targeted at development environments can be created from the `main` branch. Releases for
installation in non-development environments should be created from a Git tag named using semantic versioning. For
example, using

* `git tag v1.2.3`
* `git push --tags`

Docker images will be built automatically by GitHub Actions after pushing to the EO-DataHub repos.
