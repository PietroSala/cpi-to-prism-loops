from .parent_info import get_parent_info


def generate_module_transitions(region, root_dict, regions):
    """Generate transitions for any module based on its relationship to parent.
    
    Args:
        region (dict): The region dictionary
        root_dict (dict): The root CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines containing the opening transitions based on parent type
    """
    region_id = region['id']
    if region_id == root_dict['id']:
        return []
        
    parent_info = get_parent_info(region_id, root_dict, regions)

    parent_id = parent_info['parent_id']
    position = parent_info['position']
       
    parent = regions[parent_id]
    transitions = []
    
    if parent['type'] == 'choice':
        if position == 'true':
            transitions.extend([
                f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=2);",
                f"    [open_to_disabled_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=0);"
            ])
        else:  # false
            true_id = parent['true']['id']
            transitions.extend([
                f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} & state{true_id}=0 -> (state{region_id}'=2);",
                f"    [open_to_disabled_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} & state{true_id}=2 -> (state{region_id}'=0);"
            ])
    elif parent['type'] == 'nature':
        if position == 'true':
            probability = parent['probability']
            transitions.append(
                f"    [open_to_nature_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> {probability}:(state{region_id}'=2) + {1-probability}:(state{region_id}'=0);"
            )
        else:  # false
            true_id = parent['true']['id']
            transitions.extend([
                f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} & state{true_id}=0 -> (state{region_id}'=2);",
                f"    [open_to_disabled_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} & state{true_id}=2 -> (state{region_id}'=0);"
            ])
    elif parent['type'] == 'loop':
        # Child of loop: can be started when loop starts or when loop decides to restart
        transitions.append(f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=2);")
    else:
        transitions.append(f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=2);")

    return transitions

def generate_loop_descendant_transitions(region, root_dict, regions):
    """Generate loop descendant reset transitions for any region that is a descendant of a loop.
    
    Args:
        region (dict): The region dictionary
        root_dict (dict): The root CPI dictionary  
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines containing loop descendant transitions
    """
    region_id = region['id']
    transitions = []
    
    # Find all loop ancestors
    def find_loop_ancestors(node_id, path=[]):
        if node_id == root_dict['id']:
            return []
        
        parent_info = get_parent_info(node_id, root_dict, regions)
        if parent_info['parent_id'] is None:
            return []
            
        parent = regions[parent_info['parent_id']]
        current_path = path + [parent_info['parent_id']]
        
        loop_ancestors = []
        if parent['type'] == 'loop':
            loop_ancestors.append(parent_info['parent_id'])
            
        loop_ancestors.extend(find_loop_ancestors(parent_info['parent_id'], current_path))
        return loop_ancestors
    
    loop_ancestors = find_loop_ancestors(region_id)
    
    # For each loop ancestor, add transition to reset this region when loop child completes
    for loop_id in loop_ancestors:
        loop_region = regions[loop_id]
        child_id = loop_region['child']['id']
        
        # Only reset if this region has higher ID than the child (to avoid shuffling)
        if region_id > child_id:
            transitions.append(
                f"    [loop_child_completed_reset_{region['type']}{region_id}] state{loop_id}=3 & state{child_id}=4 & state{region_id}!=1 -> (state{region_id}'=1);"
            )
    
    return transitions

def generate_task_module(region, root_dict, regions):
    """Generate module definition for a task region.
    
    Args:
        region (dict): Task region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines of the module definition
    """
    region_id = region['id']
    lines = []
    
    lines.append(f"module task{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    lines.append(f"    step{region_id} : [0..{region['duration']}] init 0;")
    
    # Add transitions based on parent type
    lines.extend(generate_module_transitions(region, root_dict, regions))
    
    # Add loop descendant transitions
    lines.extend(generate_loop_descendant_transitions(region, root_dict, regions))
    
    # Handle step transitions based on duration
    if region['duration'] == 1:
        lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (step{region_id}'=1) & (state{region_id}'=4);")
        lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    else:
        lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (step{region_id}'=1) & (state{region_id}'=3);")
        lines.append(f"    [step] StepAvailable & state{region_id}=3 & step{region_id}<{region['duration']-1} -> (step{region_id}'=step{region_id}+1);")
        lines.append(f"    [step] StepAvailable & state{region_id}=3 & step{region_id}={region['duration']-1} -> (step{region_id}'=step{region_id}+1) & (state{region_id}'=4);")
        lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    # Add true transition for inactive states
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5) -> true;")
    
    lines.append("endmodule")
    return lines

def generate_loop_module(region, root_dict, regions):
    """Generate module definition for a loop region.
    
    Args:
        region (dict): Loop region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines of the module definition
    """
    region_id = region['id']
    child_id = region['child']['id']
    probability = region['probability']
    lines = []
    
    lines.append(f"module loop{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Add transitions based on parent type
    lines.extend(generate_module_transitions(region, root_dict, regions))
    
    # Add loop descendant transitions
    lines.extend(generate_loop_descendant_transitions(region, root_dict, regions))
    
    # Core loop transitions (atemporal)
    lines.append(f"    [loop_child_completed_loop{region_id}] LoopChildCompleted_loop{region_id} -> (state{child_id}'=1);")
    lines.append(f"    [loop_restart_child_loop{region_id}] LoopShouldRestart_loop{region_id} -> {probability}:(state{child_id}'=2) + {1-probability}:(state{child_id}'=0);")
    lines.append(f"    [loop_completed_loop{region_id}] LoopChildExcluded_loop{region_id} -> (state{region_id}'=4);")
    
    # Standard closing transition
    lines.append(f"    [running_to_completed_loop{region_id}] ActiveClosingPending_loop{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_choice_module(region, root_dict, regions):
    """Generate module definition for a choice region.
    
    Args:
        region (dict): Choice region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines of the module definition
    """
    region_id = region['id']
    lines = []
    
    lines.append(f"module choice{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Add transitions based on parent type
    lines.extend(generate_module_transitions(region, root_dict, regions))
    
    # Add loop descendant transitions
    lines.extend(generate_loop_descendant_transitions(region, root_dict, regions))
    
    lines.append(f"    [running_to_completed_choice{region_id}] ActiveClosingPending_choice{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_nature_module(region, root_dict, regions):
    """Generate module definition for a nature region.
    
    Args:
        region (dict): Nature region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines of the module definition
    """
    region_id = region['id']
    lines = []
    
    lines.append(f"module nature{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Add transitions based on parent type
    lines.extend(generate_module_transitions(region, root_dict, regions))
    
    # Add loop descendant transitions
    lines.extend(generate_loop_descendant_transitions(region, root_dict, regions))
    
    lines.append(f"    [running_to_completed_nature{region_id}] ActiveClosingPending_nature{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_sequence_module(region, root_dict, regions):
    """Generate module definition for a sequence region.
    
    Args:
        region (dict): Sequence region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines of the module definition
    """
    region_id = region['id']
    lines = []
    
    lines.append(f"module sequence{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Add transitions based on parent type
    lines.extend(generate_module_transitions(region, root_dict, regions))
    
    # Add loop descendant transitions
    lines.extend(generate_loop_descendant_transitions(region, root_dict, regions))
    
    lines.append(f"    [running_to_completed_sequence{region_id}] ActiveClosingPending_sequence{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_parallel_module(region, root_dict, regions):
    """Generate module definition for a parallel region.
    
    Args:
        region (dict): Parallel region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines of the module definition
    """
    region_id = region['id']
    lines = []
    
    lines.append(f"module parallel{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Add transitions based on parent type
    lines.extend(generate_module_transitions(region, root_dict, regions))
    
    # Add loop descendant transitions
    lines.extend(generate_loop_descendant_transitions(region, root_dict, regions))
    
    lines.append(f"    [running_to_completed_parallel{region_id}] ActiveClosingPending_parallel{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_module(region, root_dict, regions):
    """Generate appropriate module definition based on region type.
    
    Args:
        region (dict): Region dictionary
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        list: Lines of the module definition
    """
    if region['type'] == 'task':
        return generate_task_module(region, root_dict, regions)
    elif region['type'] == 'choice':
        return generate_choice_module(region, root_dict, regions)
    elif region['type'] == 'nature':
        return generate_nature_module(region, root_dict, regions)
    elif region['type'] == 'sequence':
        return generate_sequence_module(region, root_dict, regions)
    elif region['type'] == 'parallel':
        return generate_parallel_module(region, root_dict, regions)
    elif region['type'] == 'loop':
        return generate_loop_module(region, root_dict, regions)
    else:
        raise ValueError(f"Unknown region type: {region['type']}")