# CNChess
Projet de S4 

### 1. Cloner le projet
    git clone <URL_DU_REPO>
    cd CNChess

### 2. Install Ubuntu WSL (only if on windows)

### 3. Open WSL

[Instructions](https://learn.microsoft.com/en-us/windows/wsl/install)

### 4. Install docker

[Instructions](https://docs.docker.com/engine/install/ubuntu/)

### 5. Build docker image
```bash
sudo docker compose build
```

#### 6. Run code
```bash
sudo docker compose run cnchess
```

### 7. Close docker (or ctrl-c)
```bash
sudo docker compose down
```