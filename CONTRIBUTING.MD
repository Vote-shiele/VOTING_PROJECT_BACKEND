# vote-shield contribution protocol  
> Last updated: [DATE]  

## ⊛ rules  
1. **Branches**  
   - `main` → Production-ready only  
   - `dev/[feature]` → Feature branches  
   - `hotfix/[issue]` → Critical patches  

2. **Commits**  
   - Format: `[type]/[module]: message`  
     - `auth/jwt: fix token expiry check`  
     - `polls/api: add results endpoint`  
   - Atomic changes only  

3. **Code**  
   - 4-space indents (no tabs)  
   - Django REST Framework standards  
   - No secrets in commits (`.env` = auto-ban)  

## ⊛ workflow  
1. `git pull --rebase` before work  
2. Test locally:  
   ```bash
   pytest && python manage.py check --deploy
