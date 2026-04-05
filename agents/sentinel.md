## 2026-04-05 - [Option Injection in Git Subprocess]
**Vulnerability:** The worker was vulnerable to option injection in `git clone` because it used unsanitized `branch` and `repo` strings from the request payload without using the `--` command-line separator. An attacker could provide a branch name like `-u./exploit` or a repo name starting with a hyphen to inject arbitrary git options.
**Learning:** Command-line tools like `git` often interpret arguments starting with a hyphen as options. If user-controlled input is placed where an argument is expected, it must be validated and/or separated from options using `--`.
**Prevention:**
1. Implement strict regex validation for all input fields used in shell commands.
2. Use the `--` separator in subprocess calls to explicitly separate options from positional arguments.
3. Use Pydantic `field_validator` to enforce security constraints at the data model level.
