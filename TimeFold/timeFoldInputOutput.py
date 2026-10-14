import json
from pathlib import Path

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}.")
        return None

def get_assignment_status(visit_id, output_data):
    vehicles = output_data.get('modelOutput', {}).get('vehicles', [])
    unassigned_visits = output_data.get('modelOutput', {}).get('unassignedVisits', [])
    
    if visit_id in unassigned_visits:
        return "Unassigned"
    
    for vehicle in vehicles:
        for shift in vehicle.get('shifts', []):
            for item in shift.get('itinerary', []):
                if item.get('kind') == 'VISIT' and item.get('id') == visit_id:
                    return f"Assigned to {vehicle.get('id', 'N/A')}"
    return "Unassigned"

def get_unassigned_reason(visit, input_data, output_data):
    vehicles = input_data.get('modelInput', {}).get('vehicles', [])
    visit_id = visit.get('id', 'N/A')
    required_skills = {skill.get('name') for skill in visit.get('requiredSkills', [])}
    prohibited_vehicles = visit.get('prohibitedVehicles', [])
    required_vehicles = visit.get('requiredVehicles', [])
    time_windows = visit.get('timeWindows', [])
    
    reasons = []
    
    # Check for skill mismatch
    has_required_skills = False
    for vehicle in vehicles:
        vehicle_skills = {skill.get('name') for skill in vehicle.get('shifts', [{}])[0].get('skills', [])}
        if required_skills.issubset(vehicle_skills):
            has_required_skills = True
            break
    if not has_required_skills:
        reasons.append(f"No provider has required skills: {', '.join(required_skills)}")
    
    # Check for prohibited vehicles
    if prohibited_vehicles:
        available_vehicles = {v.get('id') for v in vehicles}
        if all(v_id in prohibited_vehicles for v_id in available_vehicles):
            reasons.append(f"All providers prohibited: {', '.join(prohibited_vehicles)}")
    
    # Check for required vehicles
    if required_vehicles:
        available_vehicles = {v.get('id') for v in vehicles}
        if not any(v_id in available_vehicles for v_id in required_vehicles):
            reasons.append(f"No required providers available: {', '.join(required_vehicles)}")
    
    # Check time window compatibility
    if time_windows:
        for vehicle in vehicles:
            for shift in vehicle.get('shifts', []):
                shift_start = shift.get('minStartTime')
                shift_end = shift.get('maxEndTime')
                visit_start = time_windows[0].get('minStartTime')
                visit_end = time_windows[0].get('maxEndTime')
                if shift_start and shift_end and visit_start and visit_end:
                    if not (visit_start >= shift_start and visit_end <= shift_end):
                        reasons.append("Visit time window incompatible with provider shifts")
                        break
    
    # Check output warnings
    warnings = output_data.get('run', {}).get('validationResult', {}).get('warnings', [])
    for warning in warnings:
        if visit_id in warning:
            reasons.append(warning)
    
    return "; ".join(reasons) or "No specific reason identified (possible capacity or solver constraints)"

def display_summary(input_data, output_data, input_file_name, output_file_name):
    if not input_data or not output_data:
        return

    model_input = input_data.get('modelInput', {})
    visits = model_input.get('visits', [])
    vehicles = model_input.get('vehicles', [])
    kpis = output_data.get('kpis', {})
    unassigned_visits = output_data.get('modelOutput', {}).get('unassignedVisits', [])
    
    print("\n=== Input Summary ===")
    print(f"File: {input_file_name}")
    print(f"Work Orders to Assign: {len(visits)}")
    print(f"Providers Available: {len(vehicles)}")
    
    print("\nWork Orders:")
    for i, visit in enumerate(visits, 1):
        visit_id = visit.get('id', 'N/A')
        skills = [skill.get('name', 'N/A') for skill in visit.get('requiredSkills', [])]
        print(f"  {i}. ID: {visit_id}")
        print(f"     Required Skills: {', '.join(skills) if skills else 'None'}")
        print(f"     Status: {get_assignment_status(visit_id, output_data)}")
    
    print("\nProviders:")
    for i, vehicle in enumerate(vehicles, 1):
        print(f"  {i}. ID: {vehicle.get('id', 'N/A')}")
        print(f"     Name: {vehicle.get('id', 'N/A')}")
        skills = [skill.get('name', 'N/A') for skill in vehicle.get('shifts', [{}])[0].get('skills', [])]
        print(f"     Skills: {', '.join(skills[:5]) + ('...' if len(skills) > 5 else '') if skills else 'None'}")

    print("\n=== Output Summary ===")
    print(f"File: {output_file_name}")
    print(f"Assigned Work Orders: {kpis.get('totalAssignedVisits', 'N/A')}")
    print(f"Unassigned Work Orders: {kpis.get('totalUnassignedVisits', 'N/A')}")
    print(f"Activated Providers: {kpis.get('totalActivatedVehicles', 'N/A')}")
    print(f"Total Travel Time: {kpis.get('totalTravelTime', 'N/A')}")
    print(f"Total Travel Distance: {kpis.get('totalTravelDistanceMeters', 'N/A')} meters")
    
    if unassigned_visits:
        print("\nUnassigned Work Orders:")
        for i, visit_id in enumerate(unassigned_visits, 1):
            visit = next((v for v in visits if v.get('id') == visit_id), {})
            print(f"  {i}. ID: {visit_id}")
            print(f"     Reason: {get_unassigned_reason(visit, input_data, output_data)}")
    else:
        print("\nNo Unassigned Work Orders.")

def main():
    script_dir = Path(__file__).parent
    source_dir = script_dir / 'source'
    
    if not source_dir.exists():
        print(f"Error: 'source' folder not found at {source_dir}")
        return
    
    input_files = list(source_dir.glob('*-input.json'))
    output_files = list(source_dir.glob('*-output.json'))
    
    if len(input_files) != 1 or len(output_files) != 1:
        print(f"Error: Expected one input and one output JSON in {source_dir}, found {len(input_files)} input, {len(output_files)} output")
        return
    
    input_file = input_files[0]
    input_data = load_json_file(input_file)
    
    output_file = output_files[0]
    output_data = load_json_file(output_file)
    
    display_summary(input_data, output_data, input_file.name, output_file.name)

if __name__ == "__main__":
    main()