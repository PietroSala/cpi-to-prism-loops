import traceback
import os
import json
from cpi_to_mdp.cpitospin import analyze_cpi_structure, CPIToSPINConverter

def load_cpi_file(process_name:str):
	cpi_file_path = f'CPIs/{process_name}.cpi'

	print(f"Loading CPI file: {cpi_file_path}")

	try:
		with open(cpi_file_path, 'r') as f:
			cpi_dict = json.load(f)

		print("✓ CPI file loaded successfully!")
		print(f"Root region type: {cpi_dict['type']}")
		print(f"Root region ID: {cpi_dict['id']}")

		# Pretty print the CPI structure
		print("\nCPI Structure:")
		print("=" * 50)
		print(json.dumps(cpi_dict, indent=2))
		return cpi_dict

	except FileNotFoundError:
		print(f"File not found: {cpi_file_path}")
		print("Available files in CPIs directory:")
		try:
			for f in os.listdir('CPIs'):
				if f.endswith('.cpi'):
					print(f"  - {f}")
		except:
			print("  Could not list CPIs directory")
	except Exception as e:
		print(f"❌ Error loading CPI file: {e}")
		traceback.print_exc()

	return None


def analize_cpi(cpi_dict):
	print("\nCPI Structure Analysis:")
	print("=" * 50)
	if 'cpi_dict' in locals():
		analyze_cpi_structure(cpi_dict)

	print("Converting CPI to SPIN...")
	print("=" * 50)

	try:
		converter = CPIToSPINConverter()
		spin_model = converter.convert_cpi_to_spin(cpi_dict)

		print("✓ Conversion successful!")
		print("\nSPIN Model Summary:")
		print("-" * 30)
		spin_model.print_model_summary()
		return spin_model

	except Exception as e:
		print(f"❌ Conversion failed: {e}")
		traceback.print_exc()
	return None