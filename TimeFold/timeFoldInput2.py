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

def format_location(location):
    return f"({location[0]}, {location[1]})" if location else "N/A"

def format_time_window(tw):
    min_start = tw.get('minStartTime', 'N/A')
    max_end = tw.get('maxEndTime', 'N/A')
    return f"{min_start} to {max_end}"

def display_input_summary(json_data, file_name):
    if not json_data:
        return

    model_input = json_data.get('modelInput', {})
    
    # Count work orders (visits)
    visits = model_input.get('visits', [])
    visit_count = len(visits)
    
    # Count vehicles (providers)
    vehicles = model_input.get('vehicles', [])
    vehicle_count = len(vehicles)
    
    # Print summary
    print("\n=== Field Service Routing Input Summary ===")
    print(f"File: {file_name}")
    print(f"Work Orders to Assign: {visit_count}")
    print(f"Vehicles (Providers) Available: {vehicle_count}")
    
    # Work Order Details
    print("\nWork Order Details:")
    if visit_count > 0:
        for i, visit in enumerate(visits, 1):
            print(f"  {i}. ID: {visit.get('id', 'N/A')}")
            print(f"     Name: {visit.get('name', 'N/A')}")
            print(f"     Location: {format_location(visit.get('location'))}")
            time_windows = visit.get('timeWindows', [])
            print(f"     Time Window: {format_time_window(time_windows[0]) if time_windows else 'N/A'}")
            print(f"     Service Duration: {visit.get('serviceDuration', 'N/A')}")
            skills = [skill.get('name', 'N/A') for skill in visit.get('requiredSkills', [])]
            print(f"     Required Skills: {', '.join(skills) if skills else 'None'}")
            print(f"     Priority: {visit.get('priority', 'N/A')}")
            print(f"     Pinning Requested: {visit.get('pinningRequested', 'N/A')}")
            preferred_vehicles = visit.get('preferredVehicles', [])
            print(f"     Preferred Vehicles: {', '.join(preferred_vehicles) if preferred_vehicles else 'None'}")
            prohibited_vehicles = visit.get('prohibitedVehicles', [])
            print(f"     Prohibited Vehicles: {', '.join(prohibited_vehicles) if prohibited_vehicles else 'None'}")
    else:
        print("  No work orders found.")
    
    # Vehicle (Provider) Details
    print("\nVehicle (Provider) Details:")
    if vehicle_count > 0:
        for i, vehicle in enumerate(vehicles, 1):
            print(f"  {i}. ID: {vehicle.get('id', 'N/A')}")
            print(f"     Type: {vehicle.get('vehicleType', 'N/A')}")
            shifts = vehicle.get('shifts', [])
            if shifts:
                for j, shift in enumerate(shifts, 1):
                    print(f"     Shift {j}:")
                    print(f"       ID: {shift.get('id', 'N/A')}")
                    print(f"       Start Location: {format_location(shift.get('startLocation'))}")
                    print(f"       Time Window: {shift.get('minStartTime', 'N/A')} to {shift.get('maxEndTime', 'N/A')}")
                    breaks = shift.get('requiredBreaks', [])
                    if breaks:
                        for k, break_info in enumerate(breaks, 1):
                            print(f"       Break {k}:")
                            print(f"         ID: {break_info.get('id', 'N/A')}")
                            print(f"         Duration: {break_info.get('duration', 'N/A')}")
                            print(f"         Time Window: {format_time_window(break_info)}")
                            print(f"         Cost Impact: {break_info.get('costImpact', 'N/A')}")
                    else:
                        print(f"       Required Breaks: None")
                    skills = [skill.get('name', 'N/A') for skill in shift.get('skills', [])]
                    print(f"       Skills: {', '.join(skills[:5]) + ('...' if len(skills) > 5 else '') if skills else 'None'}")
            else:
                print("     No shifts found.")
    else:
        print("  No vehicles found.")
    print("========================================")

def main():
    # Assume 'source' folder is next to the .py file
    script_dir = Path(__file__).parent
    source_dir = script_dir / 'source'
    
    # Check if source folder exists
    if not source_dir.exists():
        print(f"Error: 'source' folder not found at {source_dir}")
        return
    
    # Get JSON files in the source folder
    json_files = list(source_dir.glob('*.json'))
    if len(json_files) != 1:
        print(f"Error: Expected exactly one JSON file in {source_dir}, found {len(json_files)}")
        return
    
    # Load and display the single JSON file
    json_file = json_files[0]
    json_data = load_json_file(json_file)
    display_input_summary(json_data, json_file.name)

if __name__ == "__main__":
    main()