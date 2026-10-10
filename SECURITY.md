# Security policy

Report private security or sensitive-asset issues directly to the repository owner rather than opening a public issue.

Do not include API keys, OAuth tokens, cookies, private Drive links with embedded credentials, personal face media or voice samples in a report. Revoke any exposed credential immediately and remove it from Git history; adding it to `.gitignore` is not sufficient.

Third-party submodules are pinned, not automatically trusted. Review upstream changes before moving either pointer. Generated compatibility runtimes are disposable and should never contain secrets.
