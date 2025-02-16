import os
from pathlib import Path
from IPython.display import display, Image
import graphviz

def show_dot_model(process_name):
    """
    Renders and displays a DOT file from the models directory in a Jupyter notebook cell.
    
    Args:
        process_name (str): Name of the process (without extension)
    """
    # Define paths
    models_dir = Path("models")
    dot_path = models_dir / f"{process_name}.dot"
    
    # Check if dot file exists
    if not dot_path.exists():
        print(f"Error: DOT file not found at {dot_path}")
        return
        
    try:
        # Read the dot file content
        with open(dot_path, 'r') as f:
            dot_content = f.read()
        
        # Create a graphviz Source object
        graph = graphviz.Source(dot_content)
        
        # Render and display in the notebook
        display(graph)
        
    except Exception as e:
        print(f"Error: {str(e)}")