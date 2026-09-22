import json
from pathlib import Path

def main():
    json_path = Path("dashboard/static/world-110m.json")
    if not json_path.exists():
        print("world-110m.json not found")
        return

    data = json.loads(json_path.read_text(encoding="utf-8"))
    scale = data["transform"]["scale"]
    trans = data["transform"]["translate"]
    arcs = data["arcs"]

    def decode_arc(arc_idx):
        if arc_idx < 0:
            raw_arc = arcs[~arc_idx]
            forward = False
        else:
            raw_arc = arcs[arc_idx]
            forward = True
        coords = []
        x, y = 0, 0
        for pt in raw_arc:
            x += pt[0]
            y += pt[1]
            lon = x * scale[0] + trans[0]
            lat = y * scale[1] + trans[1]
            # Equirectangular projection for viewBox 0 0 1000 500
            px = round((lon + 180.0) * (1000.0 / 360.0), 1)
            py = round((90.0 - lat) * (500.0 / 180.0), 1)
            coords.append((px, py))
        if not forward:
            coords.reverse()
        return coords

    # 1. Generate combined land mass path
    land_geoms = data["objects"]["land"]["geometries"]
    path_commands = []
    for geom in land_geoms:
        poly_list = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
        for poly in poly_list:
            for ring in poly:
                ring_coords = []
                for arc_idx in ring:
                    pts = decode_arc(arc_idx)
                    if not ring_coords:
                        ring_coords.extend(pts)
                    else:
                        ring_coords.extend(pts[1:])
                if ring_coords:
                    cmd = f"M{ring_coords[0][0]},{ring_coords[0][1]}"
                    for pt in ring_coords[1:]:
                        cmd += f"L{pt[0]},{pt[1]}"
                    cmd += "Z"
                    path_commands.append(cmd)

    full_land_path = " ".join(path_commands)
    print(f"Generated land path with {len(path_commands)} rings, {len(full_land_path)} chars.")

    # 2. Generate per-country paths with ISO IDs & names for interactive styling
    country_geoms = data["objects"]["countries"]["geometries"]
    countries_data = []
    for geom in country_geoms:
        c_id = geom.get("id")
        c_name = geom.get("properties", {}).get("name", "Unknown")
        poly_list = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
        c_cmds = []
        for poly in poly_list:
            for ring in poly:
                ring_coords = []
                for arc_idx in ring:
                    pts = decode_arc(arc_idx)
                    if not ring_coords:
                        ring_coords.extend(pts)
                    else:
                        ring_coords.extend(pts[1:])
                if ring_coords:
                    cmd = f"M{ring_coords[0][0]},{ring_coords[0][1]}"
                    for pt in ring_coords[1:]:
                        cmd += f"L{pt[0]},{pt[1]}"
                    cmd += "Z"
                    c_cmds.append(cmd)
        if c_cmds:
            countries_data.append({
                "id": c_id,
                "name": c_name,
                "d": " ".join(c_cmds)
            })

    print(f"Decoded {len(countries_data)} countries.")
    
    # Save outputs
    out_file = Path("dashboard/static/world_paths.json")
    out_file.write_text(json.dumps({
        "land": full_land_path,
        "countries": countries_data
    }, indent=2), encoding="utf-8")
    print(f"Saved to {out_file}")

if __name__ == "__main__":
    main()
