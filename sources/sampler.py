import random

def sample_expected_impact(root_dict, track_choices=False):
    """
    Recursively calculates expected impact bounds from a process dictionary.
    
    Args:
        root_dict (dict): Process dictionary with nested structure
        track_choices (bool): If True, return choices made at each choice node
        
    Returns:
        dict or tuple: If track_choices is False, returns just the impacts dictionary.
                      If track_choices is True, returns (impacts_dict, choices_dict)
    """
    def merge_impacts(impact1, impact2):
        """
        Merges two impact dictionaries by summing values for each key.
        If a key is missing in one dictionary, assumes 0.
        """
        all_keys = set(impact1.keys()) | set(impact2.keys())
        return {
            key: impact1.get(key, 0) + impact2.get(key, 0)
            for key in all_keys
        }
    
    def scale_impacts(impacts, scale):
        """
        Multiplies all values in an impact dictionary by a scalar.
        """
        return {key: value * scale for key, value in impacts.items()}
    
    choices_made = {}
    
    def process_node(node):
        # Base case: if node is a task, return its impacts (or empty dict if none)
        if node["type"] == "task":
            return node.get("impacts", {})
            
        # Recursive cases based on node type
        if node["type"] == "sequence":
            head_impacts = process_node(node["head"])
            tail_impacts = process_node(node["tail"])
            return merge_impacts(head_impacts, tail_impacts)
            
        elif node["type"] == "parallel":
            first_impacts = process_node(node["first_split"])
            second_impacts = process_node(node["second_split"])
            return merge_impacts(first_impacts, second_impacts)
            
        elif node["type"] == "choice":
            # Randomly choose between true and false branches
            is_true = random.choice([True, False])
            chosen_branch = node["true"] if is_true else node["false"]
            
            # Record the choice if tracking is enabled
            if track_choices:
                choices_made[f"choice{node['id']}"] = is_true
                
            return process_node(chosen_branch)
            
        elif node["type"] == "nature":
            # Calculate probability-weighted impacts for both branches
            true_impacts = scale_impacts(
                process_node(node["true"]), 
                node["probability"]
            )
            false_impacts = scale_impacts(
                process_node(node["false"]), 
                1 - node["probability"]
            )
            return merge_impacts(true_impacts, false_impacts)
            
        return {}  # Default case for unknown node types
    
    impacts = process_node(root_dict)
    
    if track_choices:
        return impacts, choices_made
    return impacts