# Required `main` protection for Juriscribe

Repository-side protection is part of the Juriscribe operational DoD but cannot be enabled by runtime source code alone.

Configure a GitHub ruleset / branch protection for `main` with:

- pull request required before merge;
- required status checks: `runtime-tests (3.10)`, `runtime-tests (3.12)`, `simulation-and-saturation`;
- require branch to be up to date before merge when compatible with the repository workflow;
- block force pushes;
- block branch deletion;
- do not allow bypass except explicitly designated repository administrators for emergency recovery.

The workflow job `governance-main-provenance` is a **detection layer**, not a substitute for the server-side rule: on a push to `main`, it verifies through GitHub's API that the commit is associated with a pull request. A direct push therefore becomes CI-visible, but without GitHub branch protection the push has already occurred.
