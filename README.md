
# Very Cool Place

We will beat Amazon Web Services (they are cheap knockoffs).

## Live Site

https://awesomewebsiteservice.anvil.app

### Branch Semantics

- **Master branch (`master`)**  
  Stable, production-ready code. Direct commits are avoided; all changes arrive via pull requests.

- **Feature branches (`feature/<name>`)**  
  Used for new functionality. Created from `main` and merged back once complete and reviewed.

- **Bugfix branches (`fix/<name>` or `bugfix/<name>`)**  
  Used for resolving defects. Scoped to a single issue and merged after validation.

- **Hotfix branches (`hotfix/<name>`)**  
  Urgent fixes for production issues. Created from `main` and merged back into both `main` and any active development branches if applicable.

- **Chore branches (`chore/<name>`)**  
  Non-functional changes such as refactoring, dependency updates, or tooling adjustments.

### managing the db
currently, all passwords are stored as sha256 hashes. to reset someone password, replace the hash with the plaintext password and paste this into the database repl:

```python
from .ServerModule1 import migrate_plain_text_passwords
print(migrate_plain_text_passwords())
```

this will rehash all passwords. plain text passwords cannot be derived from a hash, so make sure the password is stored elsewhere.

a password reset flow is at the top of out priority list right now.
