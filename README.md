# CNChess - Automated Chess System
Automated chess board for playing against chess engine. For more information concerning the hardware needed visit the [wiki](https://github.com/LepTho2233127/CNChess/wiki)

## Get Started for Software Development

### 1. Clone project
    git clone <REPO_URL>

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

### 8. Run code
```bash
sudo docker compose run cnchess
```

### 9. Close docker (or ctrl-c)
```bash
sudo docker compose down
```
> [!NOTE]
> If you are on a Linux operating systems, it is possible to not use Docker by following this procedure

### 1. Install Stockfish at default location
```bash
sudo apt update
sudo apt install stockfish
which stockfish
```
>[!IMPORTANT]
>If path obtained when running which command is not /usr/games/stockfish, you need to change it in CNChess.py file manually

### 2. Install Python libraries
Inside CNChess directory run : 

```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the project
With right hardware, run this command in python directory with virtual environment activated
```bash
python main.py
```
If no camera or serial port is detected, you might need to change it respectively inside Cam.py or Communication.py.

## Documentation
Additional software documentation is available and generated using MkDocs. Run `mkdocs build` inside project directory to build it.
Located inside docs_build directory, open in a browser to access it.

