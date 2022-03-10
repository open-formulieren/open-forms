# Contribution guidelines

If you want to contribute, we ask you to follow these guidelines.

## Reporting bugs

If you have encountered a bug in this project, please check if an issue already 
exists in the list of existing [issues][issues]. If such an issue does not 
exist, you can create a [new issue][new_issue]. When writing the bug report, 
try to add a clear example that shows how to reproduce said bug.

## Adding new features

Before making making changes to the code, we advise you to first check the list 
of existing [issues][issues] for this project to see if an issue for the 
suggested changes already exists. If such an issue does not exist, you can 
create a [new issue][new_issue]. Creating an issue gives an opportunity for 
other developers to give tips even before you start coding.

### Code style

To keep the code clean and readable, this project uses:

- [`isort`](https://github.com/timothycrosley/isort) to order the imports
- [`black`](https://github.com/psf/black) to format the code and keep diffs for 
  pull requests small
- [`flake8`](https://github.com/PyCQA/flake8) to clean up code (removing unused
  imports, etc.)

Whenever a branch is pushed or a pull request is made, the code will be checked 
in CI by the tools mentioned above, so make sure to install these tools and run 
them locally before pushing branches/making pull requests.

This project aims to meet the criteria of the 
[Standard for Public Code][Standard_for_Public_Code]. Please make sure that 
your pull requests are compliant, that will make the reviews quicker.

### Forking the repository

In order to implement changes to this project when you do not have rights for 
this [repository][repository], you must first fork the repository. Once the 
repository is forked, you can clone it to your local machine.

### Making the changes

On your local machine, create a new branch, and name it like:
- `feature/some-new-feature`, if the changes implement a new feature
- `issue/some-issue`, if the changes fix an issue

Once you have made changes or additions to the code, you can commit them (try 
to keep the commit message descriptive but short). If an issue already exists 
in the list of existing [issues][issues] for the changes you made, be sure to 
format your commit message like 
`:gitmoji: Fixes #<issue_id> -- description of changes made`, where 
`<issue_id>` corresponds to the number of the issue on GitHub. To demonstrate 
that the changes implement the new feature/fix the issue, make sure to also add 
tests to the existing Django testsuite.

### Making a pull request

If all changes have been committed, you can push the branch to your fork of the 
repository and create a pull request to the `master` branch of this project's 
repository. Your pull request will be reviewed, if applicable, feedback will be 
given and if everything is approved, it will be merged.

Pull requests should always be made to the `master` branch, even if they are bugfixes
for any of the `stable/*` branches. If they are relevant for older versions, please add
the *needs-backport* label to the pull request and/or issue. Release managers will then
ensure the fix also lands in the supported older versions.

### Reviews on releases

Open Forms community support is provided by [Maykin Media][Maykin_Media]. 
The community support team is responsible for reviewing all pull requests 
before they are merged to a release branch.


[issues]: https://github.com/open-formulieren/open-forms/issues
[new_issue]: https://github.com/open-formulieren/open-forms/issues/new/choose
[mailinglist]: t.b.d.
[Standard_for_Public_Code]: https://standard.publiccode.net
[repository]: https://github.com/open-formulieren/open-forms
[Maykin_Media]: https://www.maykinmedia.nl
