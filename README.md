# fki_tools

## Overview

This repository contains various scripts to automate and simplify development workflows.

## WRclone: Python script wrapper for rclone tools 💾

### Installation

```bash
cd WRclone
python -m venv .venv
pip install -r requirements.txt
./synchrorize.py
```

## How to use 💡

Adjust the `config.json` file.

### Push
Make source and destination identical, modifying destination only.
```powershell
.\run_synchro.ps1 yoga --action push
```

### Pull
Make source and destination identical, modifying source only.
```powershell
.\run_synchro.ps1 yoga --action pull
```

## License

MIT