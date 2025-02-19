import os
from bounds import generate_multi_rewards_requirement
import subprocess

def analyze_bounds(model_name, thresholds):
    """
    Analyze a model against multi-reward bounds.
    
    Args:
        model_name (str): Name of the model file (without extension)
        thresholds (dict): Dictionary mapping impact names to threshold values
        
    Returns:
        dict: Analysis results including PRISM output and timing
        
    Example:
        analyze_bounds("test5", {"cost": 100, "time": 50})
    """
    # Ensure models directory exists
    os.makedirs('models', exist_ok=True)
    
    # Define paths
    model_path = os.path.join('models', f'{model_name}.nm')
    pctl_path = os.path.join('models', f'{model_name}.pctl')
    prism_path = "prism-4.8.1-mac64-arm/bin/prism"
    
    # Generate and write PCTL property
    property_str = generate_multi_rewards_requirement(thresholds)
    with open(pctl_path, 'w') as f:
        f.write(property_str)
    
    # Run PRISM with the model and property files
    cmd = [
        os.path.abspath(prism_path),
        os.path.abspath(model_path),
        os.path.abspath(pctl_path),
        "-verbose"
    ]
    
    try:
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        # Compile results
        analysis_info = {
            'command': ' '.join(cmd),
            'prism_output': result.stdout,
            'property': property_str,
            'return_code': result.returncode,
            'error_output': result.stderr if result.stderr else None
        }
        
        return analysis_info
        
    except subprocess.CalledProcessError as e:
        print(f"Error running PRISM: {e}")
        print(f"PRISM output: {e.output}")
        return {
            'command': ' '.join(cmd),
            'error': str(e),
            'prism_output': e.output,
            'return_code': e.returncode,
            'error_output': e.stderr if hasattr(e, 'stderr') else None
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'command': ' '.join(cmd),
            'error': str(e),
            'return_code': -1
        }