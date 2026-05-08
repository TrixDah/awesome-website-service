
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

### Managing The DataBase

#### Adding New Users
To add a new user, the new user must first authenticate with a google account. Then, one must enable their account in the database and give the new user a username. 
