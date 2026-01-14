# CNChess
Projet de S4 

AVEC POWERSHELL

1. Cloner le projet
    git clone <URL_DU_REPO>
    cd CNChess

2. Créer l’environnement virtuel (venv)
    ```bash
    python -m venv venv
    ```

3. Activer l’environnement virtuel (PowerShell)

PowerShell bloque les scripts par défaut.
Si c’est la première fois que vous activez un venv, exécutez :
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
Puis activez le venv :
```bash
    venv\Scripts\Activate.ps1
    pip install -r requirements.txt
```

5. Vérifier l’installation
    python -c "import chess, serial, numpy; print('OK')"
Si ça affiche OK, tout est fonctionnel.

8. Lancer le projet
Toujours activer le venv avant d’exécuter le code :
```bash
    powershell
    venv\Scripts\Activate.ps1
    python src/main.py
```

9. Workflow Git recommandé
```bash
    # Ajouter un fichier
    git add <fichier>
    # Commit
    git commit -m "Message clair"
    # Push
    git push
```