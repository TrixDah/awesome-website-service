<h4>Very Cool Place</h4>

We will beat Amazon Web Services (they are cheap knockoffs).

### Branch Semantics

- main (or master)  
  Stable, production-ready code. Direct commits are avoided; all changes arrive via pull requests.

- Feature branches (feature/<name>)  
  Used for new functionality. Created from main and merged back once complete and reviewed.

- Bugfix branches (fix/<name> or bugfix/<name>)  
  Used for resolving defects. Scoped to a single issue and merged after validation.

- Hotfix branches (hotfix/<name>)  
  Urgent fixes for production issues. Created from main and merged back into both main and any active development branches if applicable.

- Chore branches (chore/<name>)  
  Non-functional changes such as refactoring, dependency updates, or tooling adjustments.