import time
import stormpy


def run_storm_analysis(output_file: str, property_str: str = 'multi(R{"impact_1"}<=89 [C])', verbose=False):   
    """
    Runs STORM analysis on a model file and saves results.
    Args:
        output_file (str): Path to the model file .nm
        property_str (str): Property to be checked
        verbose (bool): Whether to print detailed logs
    Returns:
        dict: Analysis information including result and timing
    """    
    if verbose:
        print("\n=== Running STORM Analysis ===")
    storm_start_time = time.time()
    
    try:
        if verbose:
            print(f"Loading STORM model from: {output_file}")
        # Parse PRISM program
        parse_start = time.time()
        prism_program = stormpy.parse_prism_program(output_file)
        parse_time = time.time() - parse_start
        
        # Build model
        build_start = time.time()
        model = stormpy.build_model(prism_program)
        build_time = time.time() - build_start
        if verbose:
            print(f"STORM model built successfully: {model}")
        
        # Parse properties
        prop_parse_start = time.time()
        properties = stormpy.parse_properties(property_str, prism_program)
        prop_parse_time = time.time() - prop_parse_start
        if verbose:
            print(f"STORM properties parsed successfully: {properties}")
        
        # Model checking
        checking_start = time.time()
        result = stormpy.model_checking(model, properties[0])
        checking_time = time.time() - checking_start
        
        storm_total_time = time.time() - storm_start_time
        
        if verbose:
            print(f"STORM analysis result: {result}")
            print(f"\nSTORM Total Time: {storm_total_time:.3f}s")
            print(f"  - Parse program time: {parse_time:.3f}s")
            print(f"  - Build model time: {build_time:.3f}s")
            print(f"  - Parse properties time: {prop_parse_time:.3f}s")
            print(f"  - Model checking time: {checking_time:.3f}s")
        
        return {
            'result': result,
            'timings': {
                'total_elapsed': storm_total_time,
                'parse_program': parse_time,
                'build_model': build_time,
                'parse_properties': prop_parse_time,
                'model_checking': checking_time
            },
            'model_info': {
                'states': model.nr_states,
                'transitions': model.nr_transitions,
                'choices': model.nr_choices
            },
            'property': property_str,
            'model': model
        }
        
    except Exception as e:
        storm_total_time = time.time() - storm_start_time
        print(f"STORM error: {str(e)}")
        return {
            'error': str(e),
            'timings': {'total_elapsed': storm_total_time}
        }

def save_comparison_to_file(process_name: str, results: Dict[str, Any], output_dir: str = "models") -> str:
    """
    Save detailed comparison results between PRISM and STORM to a text file.
    
    Args:
        process_name: Name of the process
        results: Dictionary containing PRISM and STORM analysis results
        output_dir: Directory where to save the file
        
    Returns:
        Path to the saved file
    """
    import os
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{process_name}_comparison_storm_prism.txt")
    
    with open(output_file, 'w') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write(f"PRISM vs STORM Model Comparison Report\n")
        f.write(f"Process: {process_name}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        if 'prism' not in results or 'storm' not in results:
            f.write("ERROR: Cannot generate comparison - missing PRISM or STORM results\n")
            return output_file
        
        prism_res = results['prism']
        storm_res = results['storm']
        
        # Analysis Results
        f.write("ANALYSIS RESULTS\n")
        f.write("-" * 80 + "\n\n")
        
        f.write("PRISM Analysis:\n")
        if 'error' in prism_res:
            f.write(f"  ERROR: {prism_res['error']}\n")
        else:
            f.write(f"  Result: {prism_res.get('result', 'N/A')}\n")
            if 'timings' in prism_res and prism_res['timings']:
                f.write("  Timings:\n")
                for timing, duration in prism_res['timings'].items():
                    if isinstance(duration, (int, float)):
                        f.write(f"    {timing}: {duration:.3f}s\n")
                    else:
                        f.write(f"    {timing}: {duration}\n")
        
        f.write("\nSTORM Analysis:\n")
        if 'error' in storm_res:
            f.write(f"  ERROR: {storm_res['error']}\n")
        else:
            f.write(f"  Result: {storm_res.get('result', 'N/A')}\n")
            if 'timings' in storm_res and storm_res['timings']:
                f.write("  Timings:\n")
                for timing, duration in storm_res['timings'].items():
                    if isinstance(duration, (int, float)):
                        f.write(f"    {timing}: {duration:.3f}s\n")
                    else:
                        f.write(f"    {timing}: {duration}\n")
        
        # Model Comparison
        f.write("\n" + "=" * 80 + "\n")
        f.write("MODEL STRUCTURE COMPARISON\n")
        f.write("-" * 80 + "\n\n")
        
        # Get model info
        prism_states = prism_res.get('states_info', {}).get('total')
        prism_transitions = prism_res.get('states_info', {}).get('transitions')
        prism_choices = prism_res.get('states_info', {}).get('choices')
        
        storm_states = storm_res.get('model_info', {}).get('states')
        storm_transitions = storm_res.get('model_info', {}).get('transitions')
        storm_choices = storm_res.get('model_info', {}).get('choices')
        
        f.write("PRISM Model:\n")
        f.write(f"  States: {prism_states}\n")
        f.write(f"  Transitions: {prism_transitions}\n")
        f.write(f"  Choices: {prism_choices}\n")
        
        f.write("\nSTORM Model:\n")
        f.write(f"  States: {storm_states}\n")
        f.write(f"  Transitions: {storm_transitions}\n")
        f.write(f"  Choices: {storm_choices}\n")
        
        f.write("\nComparison:\n")
        states_match = prism_states == storm_states
        transitions_match = prism_transitions == storm_transitions
        choices_match = prism_choices == storm_choices
        
        f.write(f"  States match: {states_match} [{'MATCH' if states_match else 'DIFF'}]\n")
        f.write(f"  Transitions match: {transitions_match} [{'MATCH' if transitions_match else 'DIFF'}]\n")
        f.write(f"  Choices match: {choices_match} [{'MATCH' if choices_match else 'DIFF'}]\n")
        
        if states_match and transitions_match and choices_match:
            f.write("\n[OK] Models are IDENTICAL\n")
        else:
            f.write("\n[ERROR] Models are DIFFERENT\n")
            if not states_match:
                f.write(f"  State difference: PRISM={prism_states}, STORM={storm_states}\n")
            if not transitions_match:
                f.write(f"  Transition difference: PRISM={prism_transitions}, STORM={storm_transitions}\n")
            if not choices_match:
                f.write(f"  Choice difference: PRISM={prism_choices}, STORM={storm_choices}\n")
        
        # Detailed structure analysis (if available)
        if 'model' in storm_res:
            storm_model = storm_res['model']
            states_path = os.path.join(output_dir, f"{process_name}_states.csv")
            trans_path = os.path.join(output_dir, f"{process_name}_trans.tra")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("DETAILED STRUCTURE ANALYSIS\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("PRISM Exported Files:\n")
            f.write(f"  States file: {states_path}\n")
            f.write(f"  Transitions file: {trans_path}\n")
            
            if os.path.exists(states_path) and os.path.exists(trans_path):
                with open(states_path, 'r') as sf:
                    prism_state_count = len(sf.readlines())
                with open(trans_path, 'r') as tf:
                    prism_trans_count = len(tf.readlines()) - 1
                
                f.write(f"  States exported: {prism_state_count}\n")
                f.write(f"  Transitions exported: {prism_trans_count}\n")
                
                f.write("\nSTORM Model:\n")
                f.write(f"  Model type: {storm_model.model_type}\n")
                f.write(f"  States: {storm_model.nr_states}\n")
                f.write(f"  Transitions: {storm_model.nr_transitions}\n")
                f.write(f"  Choices: {storm_model.nr_choices}\n")
                
                f.write("\nExported Files Comparison:\n")
                if prism_state_count == storm_model.nr_states and prism_trans_count == storm_model.nr_transitions:
                    f.write("  [OK] PRISM exported files match STORM model structure!\n")
                else:
                    f.write("  [ERROR] Exported files have DIFFERENT structure:\n")
                    if prism_state_count != storm_model.nr_states:
                        f.write(f"    States: PRISM={prism_state_count}, STORM={storm_model.nr_states}\n")
                    if prism_trans_count != storm_model.nr_transitions:
                        f.write(f"    Transitions: PRISM={prism_trans_count}, STORM={storm_model.nr_transitions}\n")
            else:
                f.write("  [WARNING] Exported files not found\n")
        
        # Property information
        if 'property' in prism_res or 'property' in storm_res:
            f.write("\n" + "=" * 80 + "\n")
            f.write("PROPERTY CHECKED\n")
            f.write("-" * 80 + "\n\n")
            property_str = prism_res.get('property') or storm_res.get('property')
            f.write(f"{property_str}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    return output_file
