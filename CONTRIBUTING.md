# Contribution guidelines

If you want to contribute, we ask you to follow these guidelines.

## Reporting bugs

If you have encountered a bug in this project, please check if an issue already exists in the list
of existing [issues][issues]. If such an issue does not exist, you can create a [new
issue][new_issue]. When writing the bug report, try to add a clear example that shows how to
reproduce said bug.

## Adding new features

Before making making changes to the code, we advise you to first check the list of existing
[issues][issues] for this project to see if an issue for the suggested changes already exists. If
such an issue does not exist, you can create a [new issue][new_issue]. Creating an issue gives an
opportunity for other developers to give tips even before you start coding.

### Code style

To keep the code clean and readable, this project uses [Ruff](https://docs.astral.sh/ruff/):

```bash
ruff check . --fix
ruff format .
```

Whenever a branch is pushed or a pull request is made, the code will be checked in CI by Ruff, so
make sure to install and run it locally before pushing branches/making pull requests.

This project aims to meet the criteria of the [Standard for Public Code][standard_for_public_code].
Please make sure that your pull requests are compliant, that will make the reviews quicker.

### Forking the repository

In order to implement changes to this project when you do not have rights for this
[repository][repository], you must first fork the repository. Once the repository is forked, you can
clone it to your local machine.

### Making the changes

On your local machine, create a new branch, and name it like:

- `feature/some-new-feature`, if the changes implement a new feature
- `issue/some-issue`, if the changes fix an issue

Once you have made changes or additions to the code, you can commit them (try to keep the commit
message descriptive but short). If an issue already exists in the list of existing [issues][issues]
for the changes you made, be sure to format your commit message like
`:gitmoji: Fixes #<issue_id> -- description of changes made`, where `<issue_id>` corresponds to the
number of the issue on GitHub. To demonstrate that the changes implement the new feature/fix the
issue, make sure to also add tests to the existing Django testsuite.

#### Refactoring

You can refactor existing code as part of any issue. For example when fixing a bug or extending an
existing feature. The refactored code should be about the issue though. Please document in the
commit why you refactored the code. The part of the refactored code should typically be a separate
commit before the commit that tackles the actual issue, so they can be reviewed separately.

#### Small textual changes

For small textual changes like fixing incorrect spelling, hyperlinks, outdated information, code
documentation, etc. you don't need to create an issue. Simply create a Pull Request (see below) that
does the update.

#### Usage of typing

Python supports type annotations since a couple of versions and the entire system is still being
iterated on in the core language. Type annotations can help catch problems through static code
analysis and is in general considered a good thing to have.

Open Forms encourages the usage of type annotations, but please be pragmatic about this - for simple
primitives and straight forward usage, we expect type hints to be added. However, you can also
easily get lost in generics and complex type annotations where you end up spending more time and
energy fighting the type system than actually implementing the functional aspect of a user
story/ticket. The functional, runtime behaviour trumps the typing information and if it conflicts,
consider leaving out or postponing the type annotations.

Additionally, while we allow usage of the `typing_extensions` module, this usage is limited to
features that are not yet available in the Python version used by Open Forms but implemented in
later versions. Non-stable and/or proposal features are not allowed.

Make use of the new typing syntax, i.e. `str | None` instead of `Optional[str]`/`Union[str, None]`,
`dict[str, str]` instead of `Dict[str, str]`, etc. If you are not sure, you can refer to the typing
documentation for the type you are using, a deprecation notice will be indicated.

### Making a pull request

If all changes have been committed, you can push the branch to your fork of the repository and
create a pull request to the `main` branch of this project's repository. Your pull request will be
reviewed, if applicable, feedback will be given and if everything is approved, it will be merged.

Pull requests should always be made to the `main` branch, even if they are bugfixes for any of the
`stable/*` branches. If they are relevant for older versions, please add the _needs-backport_ label
to the pull request and/or issue. Release managers will then ensure the fix also lands in the
supported older versions.

### Reviews on releases

Open Forms community support is provided by [Maykin Media][maykin_media]. The community support team
is responsible for reviewing all pull requests before they are merged to a release branch.

[issues]: https://github.com/open-formulieren/open-forms/issues
[new_issue]: https://github.com/open-formulieren/open-forms/issues/new/choose
[mailinglist]: t.b.d.
[standard_for_public_code]: https://standard.publiccode.net
[repository]: https://github.com/open-formulieren/open-forms
[maykin_media]: https://www.maykinmedia.nl
