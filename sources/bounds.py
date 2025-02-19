def generate_multi_rewards_requirement(thresholds):
    """
    Generate a PRISM property for multi-cumulative rewards with thresholds.
    
    Args:
        thresholds (dict): Dictionary mapping impact names to their threshold values
                          e.g. {"cost": 100, "time": 50}
                          
    Returns:
        str: PRISM property checking multiple reward thresholds
    """
    # Generate individual reward bound expressions
    reward_bounds = [
        f'R{{"{impact_name}"}}<={threshold:0.6f} [C]'
        for impact_name, threshold in sorted(thresholds.items())
    ]
    
    # Combine into multi() property
    return f'multi({", ".join(reward_bounds)})'