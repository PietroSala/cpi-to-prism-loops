from .parent_info import get_parent_info

def generate_closing_pending_formula(region):
    """Generate ClosingPending formula for a region.
    
    Args:
        region (dict): Region dictionary containing type and child information
        
    Returns:
        str: The ClosingPending formula for this region
    """
    region_id = region['id']
    if region['type'] == 'task':
        return f"state{region_id}=3 & step{region_id}={region['duration']}"
    elif region['type'] == 'sequence':
        tail_id = region['tail']['id']
        return f"state{region_id}=3 & (state{tail_id}=4 | state{tail_id}=5)"
    elif region['type'] == 'parallel':
        first_id = region['first_split']['id']
        second_id = region['second_split']['id']
        return f"state{region_id}=3 & (state{first_id}=4 | state{first_id}=5) & (state{second_id}=4 | state{second_id}=5)"
    elif region['type'] == 'choice':
        true_id = region['true']['id']
        false_id = region['false']['id']
        return f"state{region_id}=3 & ((state{true_id}=4 | state{true_id}=5) | (state{false_id}=4 | state{false_id}=5))"
    return ""

def generate_ready_pending_formula(region, root_dict, regions):
    """Generate ReadyPending formula for a region.
    
    Args:
        region (dict): Region dictionary containing type and ID
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        str: The ReadyPending formula for this region, or None if root
    """
    region_id = region['id']
    
    if region_id == root_dict['id']:
        return None
        
    parent_info = get_parent_info(region_id, root_dict, regions)
    parent_id = parent_info['parent_id']
    position = parent_info['position']
    
    if parent_id is None:
        raise ValueError(f"Error: non-root region {region_id} has no parent!")
        
    parent = regions[parent_id]
    base_condition = f"state{region_id}=1"
    
    if parent['type'] == 'sequence':
        if position == 'head':
            return f"{base_condition} & state{parent_id}=2"
        else:  # tail
            head_id = parent['head']['id']
            return f"{base_condition} & (state{parent_id}=2 | state{parent_id}=3) & (state{head_id}=4 | state{head_id}=5)"
    elif parent['type'] == 'parallel':
        return f"{base_condition} & (state{parent_id}=2 | state{parent_id}=3)"
    elif parent['type'] == 'choice':
        if position == 'true':
            return f"{base_condition} & (state{parent_id}=2 | state{parent_id}=3)"
        else:  # false
            true_id = parent['true']['id']
            return f"{base_condition} & (state{parent_id}=2 | state{parent_id}=3) & (state{true_id}=0 | state{true_id}=2)"
            
    raise ValueError(f"Unknown parent type: {parent['type']}")

def generate_step_ready_formula(region):
    """Generate StepReady formula for a task region.
    
    Args:
        region (dict): Task region dictionary
        
    Returns:
        str: The StepReady formula for this task
    """
    if region['type'] != 'task':
        return None
        
    region_id = region['id']
    return f"(state{region_id}=2 | state{region_id}=3) & step{region_id} < {region['duration']}"

def generate_active_ready_pending_formula(region, root_dict, regions, region_ready_pendings):
    """Generate ActiveReadyPending formula for a region.
    
    Args:
        region (dict): Region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        region_ready_pendings (list): List of (id, type) tuples for regions with ReadyPending
        
    Returns:
        str: The ActiveReadyPending formula for this region
    """
    region_id = region['id']
    
    prev_terms = [f"!ReadyPending_{regions[prev_id]['type']}{prev_id}" 
                 for prev_id, _ in region_ready_pendings 
                 if prev_id < region_id]
    
    if prev_terms:
        return f"ReadyPending_{region['type']}{region_id} & {' & '.join(prev_terms)}"
    return f"ReadyPending_{region['type']}{region_id}"

def generate_active_closing_pending_formula(region, regions, region_closing_pendings):
    """Generate ActiveClosingPending formula for a region.
    
    Args:
        region (dict): Region dictionary
        regions (dict): Dictionary of all regions indexed by ID
        region_closing_pendings (list): List of (id, type) tuples for regions with ClosingPending
        
    Returns:
        str: The ActiveClosingPending formula for this region
    """
    region_id = region['id']
    
    prev_terms = [f"!ClosingPending_{regions[prev_id]['type']}{prev_id}" 
                 for prev_id, _ in region_closing_pendings 
                 if prev_id < region_id]
    
    if prev_terms:
        return f"ReadyPendingCleared & ClosingPending_{region['type']}{region_id} & {' & '.join(prev_terms)}"
    return f"ReadyPendingCleared & ClosingPending_{region['type']}{region_id}"