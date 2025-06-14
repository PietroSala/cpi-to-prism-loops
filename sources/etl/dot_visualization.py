
def is_passing_time(place_name, place_name_next):
	for k, v in place_name_next.items():
		if k in place_name.keys():
			if place_name[k] < v:
				return True # if passing time
	return False # if not passing time

def places_label(idx:int, places:{}):
	joined_parts = ''
	for k, v in places.items():
		joined_parts += f'{k} → {v} \n'
	return f'"{idx}" [label="{joined_parts}", style="filled", fillcolor="lightblue"];'

def impacts_label(label: list, rewards_dict: dict):
	l = []
	impact_sums = {}  # Accumulate sums for each impact

	for col in label:
		l.append(f"{col.replace('fire_', '')}")
		for impact, value in rewards_dict[col].items():
			if impact in impact_sums:
				impact_sums[impact] += value
			else:
				impact_sums[impact] = value

	# Format summed impacts as "impact_name:total_value"
	lab_impacts = [f'{impact}:{value}' for impact, value in impact_sums.items()]
	return '\n'.join(l), '\n'.join(lab_impacts)


def add_impacts(idx, label, rewards):
	l , lab_impacts = impacts_label(label, rewards)
	idx_impacts = f'{idx}i'
	return [
		f'"{idx_impacts}" [label="{l} \n {lab_impacts}", shape="box", style="filled,dashed", fillcolor="lightgrey"];',
		f'"{idx}" -> "{idx_impacts}" [style="dotted"];'
	]

def add_empty_transition(idx, idx_next):
	idx_transition = f'{idx}t'
	return [
		f'"{idx_transition}" [label="{{∅}}" , style="filled", fillcolor="lightcoral", shape="circle"];',
		f'"{idx}" -> "{idx_transition}";',
		f'"{idx_transition}" -> "{idx_next}";'
	]

def add_choice(combo, idx, idx_next):
	combo_str = '\n'.join(f'{k}{v}' for k, v in combo.items())
	idx_choice = f'{idx}c'
	return [
		f'"{idx_choice}" [label="{{{combo_str}}}" , style="filled", fillcolor="lightcoral", shape="ellipse" ];',
		f'"{idx}" -> "{idx_choice}";',
		f'"{idx_choice}" -> "{idx_next}"; '
	]

def add_nature(combo, idx, idx_next, probability):
	combo_str = '\n'.join(f'{k}{v}' for k, v in combo.items())
	idx_nature = f'{idx}n'
	prob_label = f'[label = "{probability}"]'
	return [
		f'"{idx_nature}" [label="{{{combo_str}}}" , style="filled", fillcolor="lightgreen", shape="ellipse" ];',
		f'"{idx}" -> "{idx_nature}"  {prob_label};',
		f'"{idx_nature}" -> "{idx_next}"; '
	]

def add_loop(combo, idx, idx_next, probability):
	combo_str = '\n'.join(f'{k}{v}' for k, v in combo.items())
	idx_loop = f'{idx}l'
	prob_label = f'[label = "{probability}"]'
	return [
		f'{idx_loop} [label="{{{combo_str}}}" , style="filled", fillcolor="lightgreen", shape="ellipse" ];',
		f'{idx} -> {idx_loop};',
		f'{idx_loop} -> {idx_next}  {prob_label}; '
	]