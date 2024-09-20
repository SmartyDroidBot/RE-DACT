# Project Setup Guide

## 1. Download and Install Ollama

First, download and install Ollama from https://ollama.com/download.
Once installed, open your command line and run the following command to pull the latest LLaMA model and start Ollama:

```sh
ollama pull llama3.1
ollama run llama3.1
```


## 2. Run the Install Script

To avoid conflicts with other projects, this script creates a virtual environment for this project and installs all dependencies.

### On Windows:
```sh
./install.bat
```

### On macOS/Linux:
```sh
./install.sh
```

## 3. Run the app

To run the server, use the following command:

```sh
python manage.py runserver <port>
```

