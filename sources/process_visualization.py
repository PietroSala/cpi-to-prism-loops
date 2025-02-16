def process_to_dot(region_dict):
    """
    Converts a hierarchical process region dictionary into DOT graph visualization format.
    
    Args:
        region_dict (dict): A nested dictionary representing the process structure,
                           where each region has a type and associated data
    
    Returns:
        str: A DOT graph representation of the process as a string
    """
    # Initialize DOT graph with default node shape as box
    dot_lines = ['digraph G {', '    node [shape=box];']
    
    def add_node(region):
        """
        Recursively processes a region and its children, adding appropriate nodes and edges
        to the DOT graph representation.
        
        Args:
            region (dict): Dictionary containing region information including type and connections
        """
        # Create unique node identifier combining type and ID
        node_id = f"{region['type']}{region['id']}"
        
        # Handle different node types with custom formatting
        if region['type'] == 'task':
            # For task nodes, include impact values and duration in label
            impacts_str = '\\n'.join([f"{k}: {v}" for k,v in region.get('impacts', {}).items()])
            duration_str = f"duration: {region['duration']}"
            label = f"{node_id}\\n{duration_str}\\n{impacts_str}"
            dot_lines.append(f'    {node_id} [label="{label}"];')
        
        elif region['type'] == 'nature':
            # For nature nodes, include probability in label
            label = f"{node_id}\\np={region['probability']}"
            dot_lines.append(f'    {node_id} [label="{label}"];')
        
        else:
            # For other node types, use simple identifier as label
            dot_lines.append(f'    {node_id} [label="{node_id}"];')
        
        # Process connections based on region type
        if region['type'] == 'sequence':
            # Sequence regions have head and tail connections
            head_id = f"{region['head']['type']}{region['head']['id']}"
            tail_id = f"{region['tail']['type']}{region['tail']['id']}"
            dot_lines.append(f'    {node_id} -> {head_id} [label="head"];')
            dot_lines.append(f'    {node_id} -> {tail_id} [label="tail"];')
            # Recursively process head and tail regions
            add_node(region['head'])
            add_node(region['tail'])
            
        elif region['type'] == 'parallel':
            # Parallel regions have first and second split connections
            first_id = f"{region['first_split']['type']}{region['first_split']['id']}"
            second_id = f"{region['second_split']['type']}{region['second_split']['id']}"
            dot_lines.append(f'    {node_id} -> {first_id} [label="first"];')
            dot_lines.append(f'    {node_id} -> {second_id} [label="second"];')
            # Recursively process both split regions
            add_node(region['first_split'])
            add_node(region['second_split'])
            
        elif region['type'] in ['choice', 'nature']:
            # Choice and nature regions have true and false branch connections
            true_id = f"{region['true']['type']}{region['true']['id']}"
            false_id = f"{region['false']['type']}{region['false']['id']}"
            dot_lines.append(f'    {node_id} -> {true_id} [label="true"];')
            dot_lines.append(f'    {node_id} -> {false_id} [label="false"];')
            # Recursively process both branches
            add_node(region['true'])
            add_node(region['false'])
    
    # Start processing from the root region
    add_node(region_dict)
    # Close the DOT graph
    dot_lines.append('}')
    # Join all lines into a single string
    return '\n'.join(dot_lines)