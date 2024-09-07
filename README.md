# Project Setup Guide

## 1. Run the install script with the following command

To avoid conflicts with other projects, this script creates a virtual environment for this project.

### On Windows:
```sh
./install.bat
```

### On macOS/Linux:
```sh
./install.sh
```


## 2. Install and Run Ollama

### Step 1: Install Ollama

To install Ollama, use the following command:

```sh
pip install ollama
```

### Step 2: Run Ollama

After installation, you can start Ollama by running:

```sh
ollama
```

For detailed setup instructions, visit the [Ollama website](https://www.ollama.com).

## 3. Run the app

To run the server, use the following command:

```sh
python manage.py runserver
```

