# Contribution Guidelines

Most information about developing for the project is described under the [development](./README.md#Development) section in the README.

We want to keep it as simple to contribute as possible. We make sure that to
follow our standards should be as simple as possible, and more or less
automatic. We also try to follow well defined and known standards.

## Style

We use the [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html)-style
for documenting our code.

We use automatic formatting via black that has been configured via
`pyproject.toml`.

## Committing and PR

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/).

A pull request needs approval from one of the maintainers. Feedback might be given, and if
so this must be addressed before merging. We try to stick to using suggestions,
so it's easy for you to apply the changes that we suggest. We're also open to
arguments, and our decision is not final.

## Automated checks

We use [pre-commit](https://pre-commit.com/) and GitHub Actions extensively to
make sure the code is following our standards. If these checks pass, then you
should be good to go.

We also have checks to ensure that testing coverage is above 75 %. For a pull request to be
approved, it must include tests.
