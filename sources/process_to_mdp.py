from cpi_to_mdp.formula_generators import (
    generate_closing_pending_formula,
    generate_ready_pending_formula,
    generate_step_ready_formula,
    generate_active_ready_pending_formula,
    generate_active_closing_pending_formula,
    generate_loop_specific_formulas,
    generate_step_available_formula
)
from cpi_to_mdp.module_generators import generate_module
from cpi_to_mdp.parent_info import get_parent_info
from cpi_to_mdp.rewards_generators import generate_rewards, integrate_rewards_to_mdp


def cpi_to_mdp(root_dict):
    """
    Convert a CPI (Configurable Process Instance) dictionary to an MDP (Markov Decision Process) model.
    
    Args:
        root_dict (dict): The root CPI dictionary containing the process structure
        
    Returns:
        str: The PRISM model as a string in .nm format
    """
    # Store all regions for formula generation
    regions = {}
    
    def collect_regions(node):
        """Recursively collect all regions from the CPI dictionary."""
        regions[node['id']] = node
        if node['type'] == 'sequence':
            collect_regions(node['head'])
            collect_regions(node['tail'])
        elif node['type'] == 'parallel':
            collect_regions(node['first_split'])
            collect_regions(node['second_split'])
        elif node['type'] in ['choice','nature']:
            collect_regions(node['true'])
            collect_regions(node['false'])
        elif node['type'] == 'loop':
            collect_regions(node['child'])
    
    collect_regions(root_dict)
    
    # Separate regions by type
    task_regions = [r for r in regions.values() if r['type'] == 'task']
    loop_regions = [r for r in regions.values() if r['type'] == 'loop']
    
    # Generate formula definitions
    formulas = ["mdp\n\n// Formula definitions"]
    
    # Add ClosingPending formulas
    for region_id, region in sorted(regions.items()):
        closing_pending = generate_closing_pending_formula(region)
        if closing_pending:
            formulas.append(f"formula ClosingPending_{region['type']}{region_id} = {closing_pending};")
    
    formulas.append("")
    
    # Add ReadyPending formulas for all non-root regions
    non_root_regions = [(rid, r) for rid, r in sorted(regions.items()) if rid != root_dict['id']]
    
    for region_id, region in non_root_regions:
        ready_pending = generate_ready_pending_formula(region, root_dict, regions)
        if ready_pending:
            formulas.append(f"formula ReadyPending_{region['type']}{region_id} = {ready_pending};")
    
    formulas.append("")
    
    # Add loop-specific formulas
    for region in loop_regions:
        loop_formulas = generate_loop_specific_formulas(region, regions)
        for formula_name, formula_body in loop_formulas.items():
            formulas.append(f"formula {formula_name} = {formula_body};")
    
    if loop_regions:
        formulas.append("")
    
    # Get lists of regions with ready/closing pending for later use
    ready_pending_regions = [(rid, r) for rid, r in non_root_regions 
                           if generate_ready_pending_formula(r, root_dict, regions)]
    closing_pending_regions = [(rid, r) for rid, r in sorted(regions.items())
                             if generate_closing_pending_formula(r)]
    
    # Add ReadyPendingCleared and ClosingPendingCleared formulas
    ready_pending_terms = [f"!ReadyPending_{r['type']}{rid}" for rid, r in ready_pending_regions]
    closing_pending_terms = [f"!ClosingPending_{r['type']}{rid}" for rid, r in closing_pending_regions]
    
    formulas.append(f"formula ReadyPendingCleared = {' & '.join(ready_pending_terms)};")
    formulas.append(f"formula ClosingPendingCleared = {' & '.join(closing_pending_terms)};")
    formulas.append("")
    
    # Add StepReady formulas for tasks
    for region_id, region in sorted(regions.items()):
        if region['type'] == 'task':
            formula = generate_step_ready_formula(region)
            if formula:
                formulas.append(f"formula StepReady_task{region_id} = {formula};")
    
    formulas.append("")
    
    # Add StepAvailable formula (updated to handle loops)
    step_available_formula = generate_step_available_formula(task_regions, loop_regions)
    formulas.append(f"formula StepAvailable = {step_available_formula};")
    formulas.append("")
    
    # Add ActiveReadyPending formulas
    for region_id, region in ready_pending_regions:
        formula = generate_active_ready_pending_formula(region, root_dict, regions, ready_pending_regions)
        formulas.append(f"formula ActiveReadyPending_{region['type']}{region_id} = {formula};")
    
    formulas.append("")
    
    # Add ActiveClosingPending formulas
    for region_id, region in closing_pending_regions:
        formula = generate_active_closing_pending_formula(region, regions, closing_pending_regions)
        formulas.append(f"formula ActiveClosingPending_{region['type']}{region_id} = {formula};")
    
    formulas.append("")
    
    # Generate module definitions
    modules = []
    for region_id in sorted(regions.keys()):
        region = regions[region_id]
        modules.extend(generate_module(region, root_dict, regions))
        modules.append("")
    
    # Generate labels
    labels = ["\n// Labels for formulas"]
    
    # Labels for ClosingPending
    for region_id, region in sorted(regions.items()):
        closing_pending = generate_closing_pending_formula(region)
        if closing_pending:
            label = f'label "ClosingPending_{region["type"]}{region_id}" = {closing_pending};'
            labels.append(label)
    
    labels.append("")
    
    # Labels for ReadyPending
    for region_id, region in sorted(regions.items()):
        if region_id != root_dict['id']:
            ready_pending = generate_ready_pending_formula(region, root_dict, regions)
            if ready_pending:
                label = f'label "ReadyPending_{region["type"]}{region_id}" = {ready_pending};'
                labels.append(label)
    
    labels.append("")
    
    # Labels for loop-specific formulas
    for region in loop_regions:
        loop_formulas = generate_loop_specific_formulas(region, regions)
        for formula_name, formula_body in loop_formulas.items():
            labels.append(f'label "{formula_name}" = {formula_body};')
    
    if loop_regions:
        labels.append("")
    
    # Labels for ReadyPendingCleared and ClosingPendingCleared
    labels.append(f'label "ReadyPendingCleared" = {" & ".join(ready_pending_terms)};')
    labels.append(f'label "ClosingPendingCleared" = {" & ".join(closing_pending_terms)};')
    labels.append("")
    
    # Labels for StepReady
    for region_id, region in sorted(regions.items()):
        if region['type'] == 'task':
            step_ready = generate_step_ready_formula(region)
            if step_ready:
                label = f'label "StepReady_task{region_id}" = {step_ready};'
                labels.append(label)
    
    labels.append("")
    
    # Label for StepAvailable
    labels.append(f'label "StepAvailable" = {step_available_formula};')
    labels.append("")
    
    # Labels for ActiveReadyPending
    for region_id, region in ready_pending_regions:
        formula = generate_active_ready_pending_formula(region, root_dict, regions, ready_pending_regions)
        label = f'label "ActiveReadyPending_{region["type"]}{region_id}" = {formula};'
        labels.append(label)
    
    labels.append("")
    
    # Labels for ActiveClosingPending
    for region_id, region in closing_pending_regions:
        formula = generate_active_closing_pending_formula(region, regions, closing_pending_regions)
        label = f'label "ActiveClosingPending_{region["type"]}{region_id}" = {formula};'
        labels.append(label)
    
    mdp_content = '\n'.join(formulas + modules + labels)

    # Generate and integrate rewards sections
    rewards_content = generate_rewards(root_dict)

    # Combine everything into final output
    return integrate_rewards_to_mdp(mdp_content, rewards_content)