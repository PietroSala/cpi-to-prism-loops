from .parent_info import get_parent_info


def find_loop_ancestor(region_id, root_dict, regions):
    """Find if a region is a descendant of any loop.
    
    Args:
        region_id (int): ID of the region to check
        root_dict (dict): Root of the CPI dictionary
        regions (dict): Dictionary of all regions indexed by ID
        
    Returns:
        int or None: ID of the loop ancestor, or None if no loop ancestor
    """
    def check_ancestry(node, target_id, path=[]):
        if node['id'] == target_id:
            # Found the target, check if any ancestor in path is a loop
            for ancestor_id in reversed(path):
                if regions[ancestor_id]['type'] == 'loop':
                    return ancestor_id
            return None
        
        new_path = path + [node['id']]
        
        if node['type'] == 'sequence':
            result = check_ancestry(node['head'], target_id, new_path)
            if result is not None:
                return result
            return check_ancestry(node['tail'], target_id, new_path)
        elif node['type'] == 'parallel':
            result = check_ancestry(node['first_split'], target_id, new_path)
            if result is not None:
                return result
            return check_ancestry(node['second_split'], target_id, new_path)
        elif node['type'] in ['choice', 'nature']:
            result = check_ancestry(node['true'], target_id, new_path)
            if result is not None:
                return result
            return check_ancestry(node['false'], target_id, new_path)
        elif node['type'] == 'loop':
            return check_ancestry(node['child'], target_id, new_path)
            
        return None
    
    return check_ancestry(root_dict, region_id)


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
        # Child of loop: respond to loop synchronization actions
        probability = parent['probability']
        transitions.extend([
            f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=2);",
            # When loop child completes, reset to open state
            f"    [loop_child_completed_sync{parent_id}] state{region_id}=4 -> (state{region_id}'=1);",
            # When loop makes decision, either restart or exclude (child makes the probabilistic choice)
            f"    [loop_decision_sync{parent_id}] state{region_id}=1 -> {probability}:(state{region_id}'=2) + {1-probability}:(state{region_id}'=0);",
            # When loop completes and child is excluded, reset to open
            f"    [loop_final_reset{parent_id}] state{parent_id}=4 & state{region_id}=0 -> (state{region_id}'=1);"
        ])
    else:
        transitions.append(f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=2);")

    return transitions


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
    lines = []
    
    lines.append(f"module loop{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Add transitions based on parent type
    lines.extend(generate_module_transitions(region, root_dict, regions))
    
    # Loop-specific synchronization transitions
    # When child completes, participate in sync but don't change own state
    lines.append(f"    [loop_child_completed_sync{region_id}] LoopChildCompleted_loop{region_id} -> true;")
    
    # When child is ready to restart, make the probabilistic decision
    probability = region['probability']
    lines.append(f"    [loop_decision_sync{region_id}] LoopShouldRestart_loop{region_id} -> true;")
    
    # Loop completion when child is excluded
    lines.append(f"    [running_to_completed_loop{region_id}] ActiveClosingPending_loop{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines


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
    
    # Add loop descendant reset if this task is a descendant of a loop
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        # Only reset if this task's ID is greater than the loop child ID
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    
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
    
    # Add loop descendant reset if this choice is a descendant of a loop
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        # Only reset if this choice's ID is greater than the loop child ID
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    
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
    
    # Add loop descendant reset if this nature is a descendant of a loop
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        # Only reset if this nature's ID is greater than the loop child ID
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    
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
    
    # Add loop descendant reset if this sequence is a descendant of a loop
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        # Only reset if this sequence's ID is greater than the loop child ID
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    
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
    
    # Add loop descendant reset if this parallel is a descendant of a loop
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        # Only reset if this parallel's ID is greater than the loop child ID
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    
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