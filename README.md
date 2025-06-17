# CPI to MDP Pipeline
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)

The main notebook demonstrates how to convert a Control Process Interface (CPI) dictionary that is used to calculate the strategy in https://github.com/danielamadori/PACO into a Markov Decision Process (MDP) format suitable for the PRISM model checker. We'll walk through:

Loading and examining a CPI dictionary
Understanding the conversion process
Generating PRISM code


## Prerequisites

- **Python 3.12+**
- **Prism**

    To install **Python**, follow the instructions on [Python's official website](https://www.python.org/downloads/). 

    To install **Prism**, follow the instructions on [PRISM model checker](https://www.prismmodelchecker.org/download.php) (version 4.8.1 or higher)
---

## Quick Start

1. **Python Environment Setup**
- **Using Conda**
  ```bash
  conda create --name cpi-to-prism python=3.12
  conda activate cpi-to-prism
  ```
- **Using venv**
  ```bash
  python3.12 -m venv cpi-to-prism
  source cpi-to-prism/bin/activate  # On macOS/Linux
  cpi-to-prism\Scripts\activate     # On Windows
  ```
- **Install dependencies:**
  ```bash
  pip install -r requirements.txt
  ```

2. Bind the PRISM executable to the notebook
   To use a different PRISM version, update the `PRISM_PATH`  variable in `sources/env.py` file with the path to the PRISM executable.
   The default is the one here presented.
   Example:
   To change the PRISM version to 4.8.1 for Linux 64-bit:
   ```python
   PRISM_PATH = "prism-4.8.1-linux64/bin/prism"
   ```

2. **Using docker**
   In terminal: 
     ```bash
      docker build -t dockerfile . 
      docker run -p 8888 dockerfile
      ```

## Running Benchmark

Ensure all dependencies are installed and your environment is correctly configured before running benchmarks.

### Preparing CPI Bundle

Place your CPI bundle into the `CPIs` folder. If you don't have a CPI bundle, you can create one by following the instructions in the repository [synthetic-cpi-generation](https://github.com/danielamadori/synthetic-cpi-generation), or you can download the pre-built bundle used in the paper for validation [here](https://univr-my.sharepoint.com/:f:/g/personal/emanuele_chini_univr_it/EuMjJi6L03lCp0e348YPAYwBMJ5jTGO1lojwuIlOAhpaaA?e=u9oXl1).

### Running the Script

Execute the benchmark script according to your operating system:

**Run the script**
- Linux
    ```bash
    chmod +x run_benchmark.sh
    ./run_benchmark.sh
    ```

After execution, benchmark results and logs will be generated in the main directory:

- `benchmarks.sqlite` – Benchmark results database
- `benchmarks_output.log` – Detailed benchmark execution log
