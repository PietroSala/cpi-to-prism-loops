from .parent_info import get_parent_info

def find_loop_ancestor(region_id, root_dict, regions):
    """Find if a region is a descendant of any loop.
    Returns the nearest ancestor loop's id or None.
    """
    def check_ancestry(node, target_id, path=[]):
        if node['id'] == target_id:
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
    """
    Generate transitions for a module based on its parent.
    This function also handles synchronization for loop children.
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
        probability = parent['probability']
        resets = [f"( {var}'={init} )" for var, init in get_local_resets(region)]
        reset_expr = ' & '.join(resets)
        main_update = f"(state{region_id}'=2)"
        transitions = [
            f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=2);",
            f"    [loop_child_completed_sync{parent_id}] state{region_id}=4 -> (state{region_id}'=1);"
        ]
        if reset_expr:
            trans_prob = f"{probability}:{main_update} & {reset_expr}"
        else:
            trans_prob = f"{probability}:{main_update}"
        trans_else = f"{1-probability}:(state{region_id}'=0)"
        transitions.append(
            f"    [loop_decision_sync{parent_id}] state{region_id}=1 & state{parent_id}=3 -> {trans_prob} + {trans_else};"
        )
        transitions.append(
            f"    [loop_final_reset{parent_id}] state{region_id}=0 -> (state{region_id}'=1);"
        )



    else:
        transitions.append(f"    [open_to_started_{region['type']}{region_id}] ActiveReadyPending_{region['type']}{region_id} -> (state{region_id}'=2);")
    return transitions

def get_local_resets(region):
    """
    Returns a list of (var_name, initial_value) pairs for all local variables
    that must be reset when a region (task, sequence, parallel, etc.) is re-activated by a loop.
    Extend this if you add more local variables to other region types!
    """
    resets = []
    region_id = region['id']
    if region['type'] == 'task':
        resets.append((f"step{region_id}", 0))
    # If you have other variables in future (e.g., for sequence, parallel...), add them here.
    # Example for future:
    # if region['type'] == 'sequence':
    #     resets.append((f"yourvar{region_id}", 0))
    return resets


def generate_loop_module(region, root_dict, regions):
    region_id = region['id']
    child_id = region['child']['id']
    lines = []
    lines.append(f"module loop{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    lines.extend(generate_module_transitions(region, root_dict, regions))

    lines.append(f"    [step] StepAvailable & state{region_id}=2 & state{child_id}>=2 -> (state{region_id}'=3);")

    lines.append(f"    [loop_child_completed_sync{region_id}] state{region_id}=3 & state{child_id}=4 -> true;")
    lines.append(f"    [loop_decision_sync{region_id}] state{region_id}=3 & state{child_id}=1 -> true;")
    lines.append(f"    [running_to_completed_loop{region_id}] state{region_id}=3 & state{child_id}=0 -> (state{region_id}'=4);")

    lines.append(f"    [loop_final_reset{region_id}] state{region_id}=4 & state{child_id}=0 -> true;")

    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    lines.append("endmodule")
    return lines

def generate_task_module(region, root_dict, regions):
    """Generate module definition for a task region."""
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
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    # Handle step transitions
    if region['duration'] == 1:
        lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (step{region_id}'=1) & (state{region_id}'=4);")
        lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    else:
        lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (step{region_id}'=1) & (state{region_id}'=3);")
        lines.append(f"    [step] StepAvailable & state{region_id}=3 & step{region_id}<{region['duration']-1} -> (step{region_id}'=step{region_id}+1);")
        lines.append(f"    [step] StepAvailable & state{region_id}=3 & step{region_id}={region['duration']-1} -> (step{region_id}'=step{region_id}+1) & (state{region_id}'=4);")
        lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    # Inactive states
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5) -> true;")
    lines.append("endmodule")
    return lines

def generate_choice_module(region, root_dict, regions):
    """Generate module definition for a choice region."""
    region_id = region['id']
    lines = []
    lines.append(f"module choice{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    lines.extend(generate_module_transitions(region, root_dict, regions))
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    lines.append(f"    [running_to_completed_choice{region_id}] ActiveClosingPending_choice{region_id} -> (state{region_id}'=4);")
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    lines.append("endmodule")
    return lines

def generate_nature_module(region, root_dict, regions):
    """Generate module definition for a nature region."""
    region_id = region['id']
    lines = []
    lines.append(f"module nature{region_id}")
    lines.append(f"    state{region_id} : [0..5] init {'2' if region_id == root_dict['id'] else '1'};")
    lines.extend(generate_module_transitions(region, root_dict, regions))
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    lines.append(f"    [running_to_completed_nature{region_id}] ActiveClosingPending_nature{region_id} -> (state{region_id}'=4);")
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
    lines.extend(generate_module_transitions(region, root_dict, regions))
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    lines.append(f"    [running_to_completed_sequence{region_id}] ActiveClosingPending_sequence{region_id} -> (state{region_id}'=4);")
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
    lines.extend(generate_module_transitions(region, root_dict, regions))
    loop_ancestor_id = find_loop_ancestor(region_id, root_dict, regions)
    if loop_ancestor_id is not None:
        loop_child_id = regions[loop_ancestor_id]['child']['id']
        if region_id > loop_child_id:
            lines.append(f"    [loop_child_completed_sync{loop_ancestor_id}] state{region_id}!=1 -> (state{region_id}'=1);")
    lines.append(f"    [running_to_completed_parallel{region_id}] ActiveClosingPending_parallel{region_id} -> (state{region_id}'=4);")
    lines.append(f"    [step] StepAvailable & (state{region_id}=0 | state{region_id}=1 | state{region_id}=5 | state{region_id}=3) -> true;")
    lines.append(f"    [step] StepAvailable & state{region_id}=2 -> (state{region_id}'=3);")
    lines.append(f"    [step] StepAvailable & state{region_id}=4 -> (state{region_id}'=5);")
    lines.append("endmodule")
    return lines

def generate_module(region, root_dict, regions):
    """Dispatch to the correct module generator based on region type."""
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
