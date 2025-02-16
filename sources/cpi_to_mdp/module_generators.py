from .parent_info import get_parent_info

def generate_task_module(region, root_dict, regions):
    """Generate module definition for a task region."""
    region_id = region['id']
    lines = []
    
    lines.append(f"module task{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    lines.append(f"    step{region_id} : [0..{region['duration']}] init 0;")
    
    # Get parent info for choice handling
    parent_info = get_parent_info(region_id, root_dict, regions)
    parent_id = parent_info['parent_id']
    position = parent_info['position']
    
    # Add open transitions based on parent type
    if region_id != root_dict['id']:
        if parent_id and regions[parent_id]['type'] == 'choice':
            if position == 'true':
                lines.append(f"    [open_to_started_task{region_id}] ActiveReadyPending_task{region_id} -> (state{region_id}'=2);")
                lines.append(f"    [open_to_disabled_task{region_id}] ActiveReadyPending_task{region_id} -> (state{region_id}'=0);")
            else:  # false
                true_id = regions[parent_id]['true']['id']
                lines.append(f"    [open_to_started_task{region_id}] ActiveReadyPending_task{region_id} & state{true_id}=0 -> (state{region_id}'=2);")
                lines.append(f"    [open_to_disabled_task{region_id}] ActiveReadyPending_task{region_id} & state{true_id}=2 -> (state{region_id}'=0);")
        else:
            lines.append(f"    [open_to_started_task{region_id}] ActiveReadyPending_task{region_id} -> (state{region_id}'=2);")
    
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
    """Generate module definition for a choice region."""
    region_id = region['id']
    lines = []
    
    lines.append(f"module choice{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    if region_id != root_dict['id']:
        lines.append(f"    [open_to_started_choice{region_id}] ActiveReadyPending_choice{region_id} -> (state{region_id}'=2);")
    
    lines.append(f"    [running_to_completed_choice{region_id}] ActiveClosingPending_choice{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_sequence_module(region, root_dict, regions):
    """Generate module definition for a sequence region."""
    region_id = region['id']
    lines = []
    
    lines.append(f"module sequence{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Get parent info for choice handling
    if region_id != root_dict['id']:
        parent_info = get_parent_info(region_id, root_dict, regions)
        parent_id = parent_info['parent_id']
        position = parent_info['position']
        
        if parent_id and regions[parent_id]['type'] == 'choice':
            if position == 'true':
                lines.append(f"    [open_to_started_sequence{region_id}] ActiveReadyPending_sequence{region_id} -> (state{region_id}'=2);")
                lines.append(f"    [open_to_disabled_sequence{region_id}] ActiveReadyPending_sequence{region_id} -> (state{region_id}'=0);")
            else:  # false
                true_id = regions[parent_id]['true']['id']
                lines.append(f"    [open_to_started_sequence{region_id}] ActiveReadyPending_sequence{region_id} & state{true_id}=0 -> (state{region_id}'=2);")
                lines.append(f"    [open_to_disabled_sequence{region_id}] ActiveReadyPending_sequence{region_id} & state{true_id}=2 -> (state{region_id}'=0);")
        else:
            lines.append(f"    [open_to_started_sequence{region_id}] ActiveReadyPending_sequence{region_id} -> (state{region_id}'=2);")
    
    lines.append(f"    [running_to_completed_sequence{region_id}] ActiveClosingPending_sequence{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_parallel_module(region, root_dict, regions):
    """Generate module definition for a parallel region."""
    region_id = region['id']
    lines = []
    
    lines.append(f"module parallel{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    
    # Get parent info for choice handling
    if region_id != root_dict['id']:
        parent_info = get_parent_info(region_id, root_dict, regions)
        parent_id = parent_info['parent_id']
        position = parent_info['position']
        
        if parent_id and regions[parent_id]['type'] == 'choice':
            if position == 'true':
                lines.append(f"    [open_to_started_parallel{region_id}] ActiveReadyPending_parallel{region_id} -> (state{region_id}'=2);")
                lines.append(f"    [open_to_disabled_parallel{region_id}] ActiveReadyPending_parallel{region_id} -> (state{region_id}'=0);")
            else:  # false
                true_id = regions[parent_id]['true']['id']
                lines.append(f"    [open_to_started_parallel{region_id}] ActiveReadyPending_parallel{region_id} & state{true_id}=0 -> (state{region_id}'=2);")
                lines.append(f"    [open_to_disabled_parallel{region_id}] ActiveReadyPending_parallel{region_id} & state{true_id}=2 -> (state{region_id}'=0);")
        else:
            lines.append(f"    [open_to_started_parallel{region_id}] ActiveReadyPending_parallel{region_id} -> (state{region_id}'=2);")
    
    lines.append(f"    [running_to_completed_parallel{region_id}] ActiveClosingPending_parallel{region_id} -> (state{region_id}'=4);")
    
    # Add step transitions
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    
    lines.append("endmodule")
    return lines

def generate_module(region, root_dict, regions):
    """Generate appropriate module definition based on region type."""
    if region['type'] == 'task':
        return generate_task_module(region, root_dict, regions)
    elif region['type'] == 'choice':
        return generate_choice_module(region, root_dict, regions)
    elif region['type'] == 'sequence':
        return generate_sequence_module(region, root_dict, regions)
    elif region['type'] == 'parallel':
        return generate_parallel_module(region, root_dict, regions)
    else:
        raise ValueError(f"Unknown region type: {region['type']}")