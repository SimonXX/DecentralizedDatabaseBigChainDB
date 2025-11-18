# Decentralized Database Demo Environment

Summary
- This repository contains a visual demonstration environment for interacting with a decentralized database architecture.
- It provides a reproducible Conda environment, a step-by-step setup guide, and a Streamlit-based visual demo.
- See the full setup guide at `documentation/doc.md`. 📄

Overview
This project hosts a visual demo that helps explore and interact with a decentralized database architecture. The demo is implemented with Streamlit and the repository includes an `environment.yml` file so you can reproduce the same Conda environment used for development and testing.

Key features
- Reproducible Conda environment (environment.yml)
- Streamlit visual demo
- Step-by-step configuration guide in `documentation/doc.md`

Prerequisites
- Conda (Anaconda or Miniconda) installed and available on your PATH
- Git (if cloning the repository)
- Recommended: use mamba for faster environment creation (optional)

Environment setup

1) Recreate the Conda environment
The repository includes `environment.yml` exported from the original environment. To recreate it, run:

```bash
conda env create -f environment.yml
```

2) Activate the environment
Replace `<environment_name>` with the name specified inside the `environment.yml` file:

```bash
conda activate <environment_name>
```

Notes about the Conda environment
- The `environment.yml` file was generated using:
  ```bash
  conda env export --no-builds | sed '/prefix:/d'
  ```
- The environment file already defines required dependencies and the Python version (see below).

Python version requirement
- This project relies on BigchainDB drivers which require:
  - python = 3.6.13
- Ensure the created Conda environment includes this Python version (it is declared in `environment.yml`).

Running the visual demo
From the root of the project folder, start the Streamlit demo with:

```bash
streamlit run DecentralizedDatabaseDEMO.py
```

Documentation
- Detailed, step-by-step configuration instructions are in:
  ```
  documentation/doc.md
  ```
