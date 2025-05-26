from .parent_info import get_parent_info

def generate_closing_pending_formula(region):
    """Generate ClosingPending formula for a region.
    
    Args:
        region (dict): Region dictionary containing type and ID
        
    Returns:
        str: The ClosingPending formula for this region, or empty string if not applicable
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
    elif region['type'] in ['choice', 'nature']:
        true_id = region['true']['id']
        false_id = region['false']['id']
        return f"state{region_id}=3 & ((state{true_id}=4 | state{true_id}=5) | (state{false_id}=4 | state{false_id}=5))"
    elif region['type'] == 'loop':
        child_id = region['child']['id']
        return f"state{region_id}=3 & state{child_id}=0"
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
    elif parent['type'] in ['choice', 'nature']:
        if position == 'true':
            return f"{base_condition} & (state{parent_id}=2 | state{parent_id}=3)"
        else:  # false
            true_id = parent['true']['id']
            return f"{base_condition} & (state{parent_id}=2 | state{parent_id}=3) & (state{true_id}=0 | state{true_id}=2)"
    elif parent['type'] == 'loop':
        # Child of loop: ready when loop is started or running and child should be restarted
        return f"{base_condition} & (state{parent_id}=2 | (state{parent_id}=3 & LoopShouldRestart_loop{parent_id}))"
            
    raise ValueError(f"Unknown parent type: {parent['type']}")

def generate_step_ready_formula(region):
    """Generate StepReady formula for a task region.
    
    Args:
        region (dict): Task region dictionary
        
    Returns:
        str: The StepReady formula for this task, or None if not a task
    """
    if region['type'] != 'task':
        return None
        
    region_id = region['id']
    return f"(state{region_id}=2 | state{region_id}=3) & step{region_id} < {region['duration']}"

def generate_loop_specific_formulas(region, regions):
    """Generate loop-specific formulas for loop regions.
    
    Args:
        region (dict): Loop region dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        dict: Dictionary containing loop-specific formula definitions
    """
    if region['type'] != 'loop':
        return {}
        
    region_id = region['id']
    child_id = region['child']['id']
    
    # Get all descendant IDs of the child (using ID ordering)
    def get_descendants(node):
        descendants = [node['id']]
        if node['type'] == 'sequence':
            descendants.extend(get_descendants(node['head']))
            descendants.extend(get_descendants(node['tail']))
        elif node['type'] == 'parallel':
            descendants.extend(get_descendants(node['first_split']))
            descendants.extend(get_descendants(node['second_split']))
        elif node['type'] in ['choice', 'nature']:
            descendants.extend(get_descendants(node['true']))
            descendants.extend(get_descendants(node['false']))
        elif node['type'] == 'loop':
            descendants.extend(get_descendants(node['child']))
        return descendants
    
    child_descendants = get_descendants(region['child'])
    
    return {
        f"LoopChildCompleted_loop{region_id}": f"state{region_id}=3 & state{child_id}=4",
        f"LoopShouldRestart_loop{region_id}": f"state{region_id}=3 & state{child_id}=1",
        f"LoopChildExcluded_loop{region_id}": f"state{region_id}=3 & state{child_id}=0",
        f"LoopDescendantOf_loop{region_id}": f"({' | '.join([f'id={desc_id}' for desc_id in child_descendants[1:]])})" if len(child_descendants) > 1 else "false"
    }

def generate_active_ready_pending_formula(region, root_dict, regions, ready_pending_regions):
    """Generate ActiveReadyPending formula for a region.
    
    Args:
        region (dict): Region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        ready_pending_regions (list): List of (id, type) tuples for regions with ReadyPending
        
    Returns:
        str: The ActiveReadyPending formula for this region
    """
    region_id = region['id']
    
    # Get all regions with smaller IDs that have ReadyPending
    prev_terms = [f"!ReadyPending_{regions[prev_id]['type']}{prev_id}" 
                 for prev_id, _ in ready_pending_regions 
                 if prev_id < region_id]
    
    if prev_terms:
        return f"ReadyPending_{region['type']}{region_id} & {' & '.join(prev_terms)}"
    return f"ReadyPending_{region['type']}{region_id}"

def generate_active_closing_pending_formula(region, regions, closing_pending_regions):
    """Generate ActiveClosingPending formula for a region.
    
    Args:
        region (dict): Region dictionary
        regions (dict): Dictionary of all regions indexed by ID
        closing_pending_regions (list): List of (id, type) tuples for regions with ClosingPending
        
    Returns:
        str: The ActiveClosingPending formula for this region
    """
    region_id = region['id']
    
    # Get all regions with smaller IDs that have ClosingPending
    prev_terms = [f"!ClosingPending_{regions[prev_id]['type']}{prev_id}" 
                 for prev_id, _ in closing_pending_regions 
                 if prev_id < region_id]
    
    if prev_terms:
        return f"ReadyPendingCleared & ClosingPending_{region['type']}{region_id} & {' & '.join(prev_terms)}"
    return f"ReadyPendingCleared & ClosingPending_{region['type']}{region_id}"

def generate_step_available_formula(task_regions, loop_regions):
    """Generate StepAvailable formula.
    
    Args:
        task_regions (list): List of task regions
        loop_regions (list): List of loop regions
        
    Returns:
        str: The StepAvailable formula
    """
    step_ready_terms = [f"StepReady_task{region['id']}" for region in task_regions]
    
    # Add condition that no loop transitions are pending
    loop_pending_terms = []
    for region in loop_regions:
        region_id = region['id']
        loop_pending_terms.extend([
            f"!LoopChildCompleted_loop{region_id}",
            f"!LoopShouldRestart_loop{region_id}", 
            f"!LoopChildExcluded_loop{region_id}"
        ])
    
    base_condition = "ReadyPendingCleared & ClosingPendingCleared"
    if loop_pending_terms:
        base_condition += f" & {' & '.join(loop_pending_terms)}"
    
    return f"{base_condition} & ({' | '.join(step_ready_terms)})"

def generate_ready_pending_cleared_formula(ready_pending_regions, regions):
    """Generate ReadyPendingCleared formula.
    
    Args:
        ready_pending_regions (list): List of regions with ReadyPending
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        str: The ReadyPendingCleared formula
    """
    ready_pending_terms = [f"!ReadyPending_{regions[rid]['type']}{rid}" 
                          for rid, _ in ready_pending_regions]
    return " & ".join(ready_pending_terms)

def generate_closing_pending_cleared_formula(closing_pending_regions, regions):
    """Generate ClosingPendingCleared formula.
    
    Args:
        closing_pending_regions (list): List of regions with ClosingPending
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        str: The ClosingPendingCleared formula
    """
    closing_pending_terms = [f"!ClosingPending_{regions[rid]['type']}{rid}" 
                           for rid, _ in closing_pending_regions]
    return " & ".join(closing_pending_terms)"