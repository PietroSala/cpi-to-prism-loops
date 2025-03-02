import sqlite3
import random
import json
import datetime
from read import read_cpi_bundles
from refinements import refine_bounds

def run_random_benchmark():
    """
    Runs benchmarks on randomly selected CPI bundles and records results in SQLite database.
    
    The function:
    1. Randomly selects x, y coordinates (1-10)
    2. Loads corresponding CPI bundle
    3. Randomly selects a dictionary from the bundle
    4. Records experiment metadata in SQLite database
    5. Runs refinement analysis
    6. Updates completion timestamp
    """
    
    # Set up SQLite database and table
    conn = sqlite3.connect('benchmarks.sqlite')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiments (
            x INTEGER,
            y INTEGER,
            w INTEGER,
            z INTEGER,
            num_impacts INTEGER,
            choice_distribution REAL,
            generation_mode TEXT,
            duration_interval_min INTEGER,
            duration_interval_max INTEGER,
            vts TIMESTAMP,
            vte TIMESTAMP,
            PRIMARY KEY (x, y, w)
        )
    ''')
    conn.commit()
    
    while True:
        try:
            # Random x, y selection (1-10)
            x = random.randint(1, 10)
            y = random.randint(1, 10)
            
            # Load CPI bundle
            bundle = read_cpi_bundles(x=x, y=y)
            
            if not bundle:
                print(f"No bundle found for x={x}, y={y}")
                continue
                
            # Random position selection
            w = random.randint(0, len(bundle) - 1)
            
            # Check if experiment already exists
            cursor.execute(
                "SELECT COUNT(*) FROM experiments WHERE x=? AND y=? AND w=?", 
                (x, y, w)
            )
            if cursor.fetchone()[0] > 0:
                print(f"Experiment x={x}, y={y}, w={w} already exists, trying another...")
                continue
                
            # Get dictionary and metadata
            D = bundle[w].copy()
            T = D.pop('metadata')
            
            # Write to current_benchmark.cpi
            with open('CPIs/current_benchmark.cpi', 'w') as f:
                json.dump(D, f)
            
            # Record start time
            vts = datetime.datetime.now().isoformat()
            
            # Insert initial record
            cursor.execute(
                """
                INSERT INTO experiments (
                    x, y, w, z, num_impacts, choice_distribution, 
                    generation_mode, duration_interval_min, duration_interval_max,
                    vts
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    x, y, w, 
                    T['z'],
                    T['num_impacts'],
                    T['choice_distribution'],
                    T['generation_mode'],
                    T['duration_interval'][0],
                    T['duration_interval'][1],
                    vts
                )
            )
            conn.commit()
            
            # Run refinement analysis
            print(f"\nRunning benchmark for x={x}, y={y}, w={w}")
            refine_bounds('current_benchmark', 10, verbose=True)
            
            # Record end time
            vte = datetime.datetime.now().isoformat()
            
            # Update record with end time
            cursor.execute(
                """
                UPDATE experiments 
                SET vte = ? 
                WHERE x = ? AND y = ? AND w = ?
                """,
                (vte, x, y, w)
            )
            conn.commit()
            
            print(f"\nCompleted benchmark x={x}, y={y}, w={w}")
            print(f"Metadata: {T}")
            print(f"Start time: {vts}")
            print(f"End time: {vte}")
            
        except Exception as e:
            print(f"Error during benchmark: {str(e)}")
            conn.rollback()
            
        # Continue with next iteration regardless of success/failure
        print("\nStarting next benchmark...")