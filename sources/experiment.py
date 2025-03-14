import datetime
import json

from sources.refinements import refine_bounds


def single_execution(cursor, conn, x, y, w, bundle):
    # Check if experiment already exists
    cursor.execute(
        "SELECT COUNT(*) FROM experiments WHERE x=? AND y=? AND w=?",
        (x, y, w)
    )
    if cursor.fetchone()[0] > 0:
        print(f"Experiment x={x}, y={y}, w={w} already exists, trying another...")
        return

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
