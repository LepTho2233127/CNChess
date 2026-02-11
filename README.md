# CNChess
Projet de S4 

### 1. Clone project
    git clone <URL_DU_REPO>

### 2. Install Ubuntu WSL (only if on windows)

[Instructions](https://learn.microsoft.com/en-us/windows/wsl/install)

### 3. Open WSL inside project folder

### 4. Install docker

```bash
sudo apt update && sudo apt upgrade
```

[Instructions](https://docs.docker.com/engine/install/ubuntu/)

### 5. If on WSL, give access to USB port to WSL 

```bash
winget install --interactive --exact dorssel.usbipd-win
```

> [!IMPORTANT]
> Run the following commands as admin in PowerShell. You also need to keep a WSL active

```PowerShell
usbipd list
usbipd bind --busid 4-4
usbipd attach --wsl --busid <busid>
```

In WSL, check if you see the device you just attached
```bash
lsusb
```

### 6. Build docker image
```bash
sudo docker compose build
```

### 7. Give docker access to window 
```bash
xhost +local:docker
```

#### 8. Run code
```bash
sudo docker compose run cnchess
```

### 9. Close docker (or ctrl-c)
```bash
sudo docker compose down
```