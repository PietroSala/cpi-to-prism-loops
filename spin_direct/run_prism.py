from datetime import datetime
import json
import os
import re
import subprocess
# https://www.prismmodelchecker.org/manual/Appendices/ExplicitModelFiles#tra
# https://www.prismmodelchecker.org/manual/RunningPRISM/ExportingTheModel#formats


def run_prism_analysis(process_name, PRISM_PATH = ''):
    """
    Runs PRISM analysis on a model file and saves results.

    Args:
        process_name (str): Name of the process (without extension)

    Returns:
        dict: Analysis information including modules, variables, and timing
    """
    # Define paths
    os.makedirs(os.path.join("../results/"), exist_ok=True)
    os.makedirs(os.path.join("../results/", f"{process_name}"), exist_ok=True)
    model_path = os.path.join("../models", f"{process_name}.nm")
    dot_path = os.path.join("../results", f"{process_name}/{process_name}.dot")
    info_path = os.path.join("../results", f"{process_name}/{process_name}.info")
    cpi_path = os.path.join("../CPIs", f"{process_name}.cpi")    
    states_path = os.path.join("../results", f"{process_name}/{process_name}_states.csv")
    trans_path = os.path.join("../results", f"{process_name}/{process_name}_trans.tra")    
    
    # Read CPI file to get task impacts
    with open(cpi_path, 'r') as f:
        cpi_data = json.load(f)

    def get_task_impacts(region):
        """
        Recursively collect task impacts from CPI data.
        Returns the complete impacts dictionary for each task.
        """
        impacts = {}
        if region["type"] == "task" and "impacts" in region:
            task_id = f"task{region['id']}"
            impacts[task_id] = region["impacts"]  # Store the complete impacts dictionary
        for key in ["head", "tail", "first_split", "second_split", "true", "false"]:
            if key in region and region[key] is not None:
                impacts.update(get_task_impacts(region[key]))
        return impacts

    # Run PRISM command
    cmd = [
        # os.path.abspath(PRISM_PATH),
        'prism',
        os.path.abspath(model_path),
        "-exporttransdotstates",
        os.path.abspath(dot_path),
        "-exportstates",
        os.path.abspath(states_path),
        "-exporttrans",
        os.path.abspath(trans_path),
        "-verbose"
    ]
    print(f"Running PRISM command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd,
                                capture_output=True,
                                text=True,
                                check=True)

        output = result.stdout

        # Extract information using regex
        modules_match = re.search(r'Modules:\s+(.+?)\n', output)
        variables_match = re.search(r'Variables:\s+(.+?)\n', output)
        time_match = re.search(r'Time for model construction: (.+?) seconds', output)

        # Compile information
        info = {
            'timestamp': datetime.now().isoformat(),
            'modules': modules_match.group(1).split() if modules_match else [],
            'variables': variables_match.group(1).split() if variables_match else [],
            'task_impacts': get_task_impacts(cpi_data),
            'model_build_time': float(time_match.group(1)) if time_match else None,
            'command': ' '.join(cmd),
            'prism_output': output
        }

        # Save information to JSON file
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)

        print(f"Analysis complete. Results saved to {info_path}")
        return info

    except subprocess.CalledProcessError as e:
        print(f"Error running PRISM: {e}")
        print(f"PRISM output: {e.output}")
        print(f"PRISM stdout: {e.stdout}")
        print(f"PRISM stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
