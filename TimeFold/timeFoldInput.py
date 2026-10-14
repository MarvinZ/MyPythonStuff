# save as list_wo_providers_detailed.py
import json, os, sys, glob

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_value(d, path_list):
    for path in path_list:
        cur = d
        ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok:
            return cur
    return None

def parse_file(path):
    data = read_json(path)
    vehicles = get_value(data, [["modelInput","vehicles"],["vehicles"]])
    visits = get_value(data, [["modelInput","visits"],["visits"],["jobs"]])
    return vehicles if isinstance(vehicles, list) else [], visits if isinstance(visits, list) else []

def print_vehicle(v):
    vid = v.get("id") or v.get("name")
    vtype = v.get("vehicleType","")
    shifts = v.get("shifts",[])
    print(f"  - ID: {vid} | Type: {vtype} | Shifts: {len(shifts)}")
    for s in shifts:
        sid = s.get("id")
        start = s.get("minStartTime")
        end = s.get("maxEndTime")
        loc = s.get("startLocation")
        print(f"      Shift: {sid} | Start: {start} | End: {end} | Location: {loc}")

def print_visit(v):
    vid = v.get("id")
    name = v.get("name","")
    loc = v.get("location","")
    dur = v.get("serviceDuration","")
    tw = v.get("timeWindows",[])
    skills = v.get("requiredSkills",[])
    print(f"  - WO ID: {vid} | Name: {name} | Duration: {dur} | Location: {loc}")
    if tw:
        for t in tw:
            print(f"      TimeWindow: {t.get('minStartTime')} -> {t.get('maxEndTime')}")
    if skills:
        skill_names = [s.get("name") for s in skills]
        print(f"      Required Skills: {', '.join(skill_names)}")

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base, "Source")
    if not os.path.isdir(source_dir):
        print("Source folder not found next to this .py")
        sys.exit(1)
    files = sorted(glob.glob(os.path.join(source_dir, "*.json")))
    if not files:
        print("No .json files in Source")
        sys.exit(0)

    for fp in files:
        print("="*80)
        print(f"File: {os.path.basename(fp)}")
        try:
            vehicles, visits = parse_file(fp)
            print(f"\nProviders ({len(vehicles)}):")
            for v in vehicles:
                print_vehicle(v)
            print(f"\nWork Orders ({len(visits)}):")
            for v in visits:
                print_visit(v)
        except Exception as e:
            print(f"Error reading {os.path.basename(fp)}: {e}")
    sys.exit(0)

if __name__ == "__main__":
    main()
