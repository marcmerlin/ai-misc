#!/usr/bin/env python3

# Copyright 2026 Marc MERLIN <marc@merlins.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Written by Google Gemini in Pro High mode under my supervision and testing.
# ----------------------------------------------------------------------------------------
#
# You need timezonefinder, you can install in a python venv, or simply like this on debian:
# pip install timezonefinder --break-system-packages

# Collecting timezonefinder
#   Downloading timezonefinder-9.0.0-cp311-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (12 kB)
# Requirement already satisfied: numpy>=2 in /usr/lib/python3/dist-packages (from timezonefinder) (2.2.4)
# Collecting h3>=4 (from timezonefinder)
#   Downloading h3-4.5.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (17 kB)
# Collecting cffi<3,>=1.15.1 (from timezonefinder)
#   Downloading cffi-2.1.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.5 kB)
# Collecting flatbuffers>=25.2.10 (from timezonefinder)
#   Downloading flatbuffers-25.12.19-py2.py3-none-any.whl.metadata (1.0 kB)
# Collecting timezonefinder-data<4,>=3.2026.3.post1 (from timezonefinder)
#   Downloading timezonefinder_data-3.2026.4-py3-none-any.whl.metadata (33 kB)
# Collecting pycparser (from cffi<3,>=1.15.1->timezonefinder)
#   Downloading pycparser-3.11-py3-none-any.whl.metadata (8.2 kB)
# Downloading timezonefinder-9.0.0-cp311-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (148 kB)
# Downloading cffi-2.1.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (221 kB)
# Downloading timezonefinder_data-3.2026.4-py3-none-any.whl (32.7 MB)
# Downloading flatbuffers-25.12.19-py2.py3-none-any.whl (26 kB)
# Downloading h3-4.5.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (1.1 MB)
# Downloading pycparser-3.11-py3-none-any.whl (51 kB)
# Installing collected packages: flatbuffers, timezonefinder-data, pycparser, h3, cffi, timezonefinder
# Successfully installed cffi-2.1.1 flatbuffers-25.12.19 h3-4.5.0 pycparser-3.11 timezonefinder-9.0.0 timezonefinder-data-3.2026.4

import xml.etree.ElementTree as ET
import glob
import argparse
import bisect
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder

SCRIPT_VERSION = "v7"

def parse_gpx_points(gpx_pattern):
    gpx_files = glob.glob(gpx_pattern)
    points = []
    
    if not gpx_files:
        return points

    print("Initializing offline timezone engine...")
    tf = TimezoneFinder()
    
    for gpx_file in gpx_files:
        try:
            tree = ET.parse(gpx_file)
            root = tree.getroot()
            for elem in root.iter():
                if elem.tag.endswith('trkpt') or elem.tag.endswith('wpt'):
                    lat = elem.get('lat')
                    lon = elem.get('lon')
                    time_elem = None
                    for child in elem:
                        if child.tag.endswith('time'):
                            time_elem = child
                            break
                            
                    if lat and lon and time_elem is not None and time_elem.text:
                        time_str = time_elem.text.strip().replace('Z', '')
                        if '.' in time_str:
                            time_str = time_str.split('.')[0]
                            
                        try:
                            f_lat, f_lon = float(lat), float(lon)
                            utc_dt = datetime.fromisoformat(time_str)
                            
                            tz_name = tf.timezone_at(lng=f_lon, lat=f_lat)
                            if tz_name:
                                tz = ZoneInfo(tz_name)
                                local_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                                local_naive = local_dt.replace(tzinfo=None)
                            else:
                                offset_hours = round(f_lon / 15.0)
                                local_naive = utc_dt + timedelta(hours=offset_hours)

                            points.append({
                                'lat': lat, 
                                'lon': lon, 
                                'utc_time': utc_dt,
                                'local_time': local_naive
                            })
                        except ValueError:
                            continue
        except Exception as e:
            print(f"Error parsing GPX {gpx_file}: {e}")
    
    points.sort(key=lambda p: p['local_time'])
    return points

def get_site_info(dive, sites_by_uuid, parent_map):
    site_name = None
    site_uuid = dive.get('siteid') or dive.get('divesiteid')
    loc_elem = dive.find('location')
    
    if not site_uuid and loc_elem is not None:
        site_uuid = loc_elem.get('uuid')
        
    if site_uuid:
        site_uuid = site_uuid.strip()
        
    target_site = sites_by_uuid.get(site_uuid)
    
    if target_site is not None:
        if target_site.get('name'):
            site_name = target_site.get('name').strip()
        elif target_site.find('name') is not None and target_site.find('name').text:
            site_name = target_site.find('name').text.strip()
            
    if not site_name and loc_elem is not None:
        if loc_elem.text and loc_elem.text.strip():
            site_name = loc_elem.text.strip()
        elif loc_elem.get('name'):
            site_name = loc_elem.get('name').strip()
            
    if not site_name:
        for attr in ['location', 'site', 'name', 'divesite']:
            if dive.get(attr):
                site_name = dive.get(attr).strip()
                break

    # If the individual dive is totally blank, inherit the location from the parent <trip> tag
    if not site_name:
        parent = parent_map.get(dive)
        if parent is not None and parent.tag == 'trip':
            if parent.get('location'):
                site_name = parent.get('location').strip()

    return site_name or "Unknown Location", target_site, loc_elem

def add_gps_to_dives(ssrf_file, gpx_points, output_file, max_delta_hours=24):
    try:
        tree = ET.parse(ssrf_file)
    except Exception as e:
        print(f"Error parsing Subsurface log {ssrf_file}: {e}")
        return

    root = tree.getroot()
    
    # Build a parent map to climb the tree for missing <trip> locations
    parent_map = {c: p for p in root.iter() for c in p}
    
    sites_by_uuid = {}
    for site in root.iter('site'):
        uuid = site.get('uuid')
        if uuid:
            sites_by_uuid[uuid.strip()] = site

    modified_count = 0
    max_delta = timedelta(hours=max_delta_hours)
    gpx_local_times = [p['local_time'] for p in gpx_points]
    
    unmatched_dives = []
    
    for dive in root.iter('dive'):
        d_date = dive.get('date')
        d_time = dive.get('time')
        d_number = dive.get('number', 'N/A')
        
        if not d_date or not d_time:
            continue
            
        try:
            dive_local_dt = datetime.strptime(f"{d_date} {d_time}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        site_name, target_site, loc_elem = get_site_info(dive, sites_by_uuid, parent_map)
        has_gps = False
        
        if dive.get('gps'):
            has_gps = True
        elif target_site is not None:
            if target_site.get('gps'):
                has_gps = True
            else:
                geo = target_site.find('geography')
                if geo is not None and geo.get('gps'):
                    has_gps = True
        elif loc_elem is not None and loc_elem.get('gps'):
            has_gps = True

        if has_gps:
            continue

        if not gpx_points:
            unmatched_dives.append({'number': d_number, 'site': site_name})
            continue

        idx = bisect.bisect_left(gpx_local_times, dive_local_dt)
        
        candidates = []
        if idx < len(gpx_points):
            candidates.append(gpx_points[idx])
        if idx > 0:
            candidates.append(gpx_points[idx - 1])

        if not candidates:
            unmatched_dives.append({'number': d_number, 'site': site_name})
            continue

        closest_point = min(candidates, key=lambda p: abs(p['local_time'] - dive_local_dt))
        min_diff = abs(closest_point['local_time'] - dive_local_dt)

        if min_diff <= max_delta:
            lat = closest_point['lat']
            lon = closest_point['lon']
            gps_str = f"{lat} {lon}"
            
            print(f"Dive #{d_number} ({site_name[:40]}) matched to Local GPX time {closest_point['local_time']} "
                  f"[diff: {min_diff}]. Assigning GPS: {gps_str}")
            
            if target_site is not None:
                geo = target_site.find('geography')
                if geo is not None:
                    geo.set('gps', gps_str)
                else:
                    target_site.set('gps', gps_str)
            else:
                if loc_elem is None:
                    loc_elem = ET.SubElement(dive, 'location')
                loc_elem.set('gps', gps_str)
                
            modified_count += 1
        else:
            unmatched_dives.append({'number': d_number, 'site': site_name})
            
    # --- Output Results ---
    if modified_count > 0:
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print(f"\nSuccessfully auto-matched and added GPS data to {modified_count} dive(s).")
    elif gpx_points:
        print("\nNo matching GPX points found within the threshold, or all dives already have GPS.")
        
    if unmatched_dives:
        print("\n--- Dives Still Missing GPS Tags ---")
        for u in unmatched_dives:
            print(f"Dive #{u['number']}: {u['site']}")
            
        unique_missing_sites = sorted(list(set([u['site'] for u in unmatched_dives])))
        print("\n--- Unique Locations Missing GPS ---")
        for site in unique_missing_sites:
            print(f"- {site}")
        print(f"\nTotal unique missing locations: {len(unique_missing_sites)}")
    else:
        print("\nAll dives in the log have GPS coordinates! No missing locations.")

    print("\n" + "="*50)
    print(f"VERSION: {SCRIPT_VERSION}")
    print(f"OUTPUT_FILE: {output_file}")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-timezone matching for GPX waypoints to Subsurface dives.")
    parser.add_argument("ssrf_file", help="Path to the Subsurface .ssrf log file")
    parser.add_argument("--gpx", default="", help="Glob pattern for GPX files (e.g., '/path/to/*.gpx'). Leave empty to just audit missing GPS.")
    parser.add_argument("--out", default="updated_divelog.ssrf", help="Output file name")
    parser.add_argument("--max-hours", type=float, default=24.0, 
                        help="Maximum hour difference allowed between dive time and GPX point.")
    
    args = parser.parse_args()
    
    points = []
    if args.gpx:
        print(f"Loading GPX files from pattern: {args.gpx}")
        points = parse_gpx_points(args.gpx)
        if points:
            print(f"Calculated local timezones for {len(points)} GPS points.\n")
        else:
            print("No valid GPX points found. Proceeding with audit only.\n")
    else:
        print("No GPX pattern provided. Auditing log for missing GPS...\n")
        
    add_gps_to_dives(args.ssrf_file, points, args.out, max_delta_hours=args.max_hours)
