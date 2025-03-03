# CPI to MDP Pipeline
The main notebook demonstrates how to convert a Control Process Interface (CPI) dictionary that is used to calculate the strategy in https://github.com/danielamadori98/PACO into a Markov Decision Process (MDP) format suitable for the PRISM model checker. We'll walk through:

Loading and examining a CPI dictionary
Understanding the conversion process
Generating PRISM code

## Prism version
To use a different PRISM version, update the *prism_path* variable (the path to the PRISM executable).
The default is the one here presented.


Example:
    To change the PRISM version to 4.9.0 for Linux 64-bit:    
    ```python
    prism_path = "prism-4.9.0-linux64/bin/prism"
    ```
