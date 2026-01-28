# CNChess
Projet de S4 

### 1. Clone projet
    git clone <URL_DU_REPO>

### 2. Install Ubuntu WSL (only if on windows)

[Instructions](https://learn.microsoft.com/en-us/windows/wsl/install)

### 3. Open WSL inside project folder

### 4. Install docker

[Instructions](https://docs.docker.com/engine/install/ubuntu/)

### 5. Build docker image
```bash
sudo docker compose build
```

### 6. Give docker access to window 
```bash
xhost +local:docker
```

#### 7. Run code
```bash
sudo docker compose run cnchess
```

### 8. Close docker (or ctrl-c)
```bash
sudo docker compose down
```