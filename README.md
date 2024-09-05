# Project Setup Guide

## 1. Create a Virtual Environment

To avoid conflicts with other projects, it's recommended to create a virtual environment for this project.

### On Windows:
```sh
py -m venv venv
```

### On macOS/Linux:
```sh
python3 -m venv venv
```

## 2. Activate the Virtual Environment

### On Windows:
```sh
.\venv\Scripts\activate
```

### On macOS/Linux:
```sh
source venv/bin/activate
```

You should now see the `(venv)` prefix in your terminal, indicating that the virtual environment is active.

## 3. Install Dependencies

With the virtual environment activated, install the required Python packages using `requirements.txt`:

```sh
pip install -r requirements.txt
```

## 4. Install and Run Ollama

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
