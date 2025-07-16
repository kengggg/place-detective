#!/usr/bin/env python3
"""
Place Detective - Advanced place investigation tool for OpenStreetMap data.

A powerful detective tool to investigate suspicious place patterns, similar spellings, and
potential data inconsistencies in OpenStreetMap across different cities and regions.
"""

import requests
import json
import pandas as pd
from fuzzywuzzy import fuzz
import re
from typing import List, Dict, Tuple, Optional
import time
import sys
import argparse
import os
from datetime import datetime

# Color support
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)  # Auto-reset colors after each print
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama is not available
    class MockColor:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = MockColor()
    COLORS_AVAILABLE = False

# Color helper functions
def print_success(text):
    """Print success message in green"""
    print(f"{Fore.GREEN}{Style.BRIGHT}✅ {text}{Style.RESET_ALL}")

def print_info(text):
    """Print info message in blue"""
    print(f"{Fore.BLUE}{Style.BRIGHT}🔍 {text}{Style.RESET_ALL}")

def print_warning(text):
    """Print warning message in yellow"""
    print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️  {text}{Style.RESET_ALL}")

def print_error(text):
    """Print error message in red"""
    print(f"{Fore.RED}{Style.BRIGHT}❌ {text}{Style.RESET_ALL}")

def print_detective(text):
    """Print detective message in magenta"""
    print(f"{Fore.MAGENTA}{Style.BRIGHT}🕵️  {text}{Style.RESET_ALL}")

def print_location(text):
    """Print location message in cyan"""
    print(f"{Fore.CYAN}{Style.BRIGHT}📍 {text}{Style.RESET_ALL}")

def print_file(text):
    """Print file message in green"""
    print(f"{Fore.GREEN}{Style.BRIGHT}📁 {text}{Style.RESET_ALL}")

def print_header(text):
    """Print header with background"""
    print(f"{Back.BLUE}{Fore.WHITE}{Style.BRIGHT} {text} {Style.RESET_ALL}")

def install_packages():
    """Install required packages if not already installed"""
    try:
        import requests
        import pandas as pd
        from fuzzywuzzy import fuzz
        return True
    except ImportError:
        print_info("Installing required packages...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "pandas", "fuzzywuzzy[speedup]", "colorama"])
            return True
        except subprocess.CalledProcessError:
            print_error("Failed to install packages. Please install manually:")
            print("pip install requests pandas fuzzywuzzy[speedup] colorama")
            return False

# City-level bounding boxes (focused, faster searches)
CITY_BBOXES = {
    "bangkok": "13.5,100.1,14.2,100.9",           # Greater Bangkok Metropolitan Area
    "chiangmai": "18.6,98.8,19.0,99.1",           # Chiang Mai city and key districts  
    "phuket": "7.7,98.2,8.3,98.5",                # Phuket Island complete coverage
    "pattaya": "12.8,100.8,13.1,101.0",           # Pattaya-Chonburi coastal region
    "chiangrai": "19.8,99.7,20.0,100.2",          # Chiang Rai city and surrounding area
    "hatyai": "6.9,100.4,7.1,100.6",              # Hat Yai city in Songkhla province
    "korat": "14.8,102.0,15.0,102.2",             # Nakhon Ratchasima (Korat) city
    "thailand": "5.6,97.3,20.5,105.6"             # Thailand complete country boundaries
}

# Province-level bounding boxes (comprehensive, longer searches with chunking)
PROVINCE_BBOXES = {
    "bangkok": "13.4,100.0,14.3,101.0",           # Bangkok + surrounding provinces
    "chiangmai": "17.8,97.8,20.5,99.6",           # Chiang Mai province complete
    "phuket": "7.6,98.1,8.4,98.6",                # Phuket province + nearby islands
    "pattaya": "12.5,100.5,13.4,101.2",           # Chonburi province coastal area
    "chiangrai": "19.3,99.4,20.5,100.5",          # Chiang Rai province
    "hatyai": "6.6,100.1,7.3,100.8",              # Songkhla province southern area
    "korat": "14.2,101.5,15.8,102.8",             # Nakhon Ratchasima province
    "thailand": "5.6,97.3,20.5,105.6"             # Thailand complete country boundaries
}

# Common OSM place types
PLACE_TYPES = {
    "amenity": ["restaurant", "cafe", "bar", "hospital", "school", "bank", "hotel", "shop"],
    "shop": ["supermarket", "convenience", "mall", "department_store", "bakery", "butcher"],
    "leisure": ["park", "garden", "sports_centre", "fitness_centre", "swimming_pool"],
    "tourism": ["hotel", "guest_house", "attraction", "museum", "viewpoint"],
    "healthcare": ["hospital", "clinic", "pharmacy", "dentist", "veterinary"],
    "education": ["school", "university", "college", "kindergarten", "library"]
}

# Overpass API endpoint
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def calculate_bbox_area(bbox_str: str) -> float:
    """Calculate the area of a bounding box in square degrees"""
    south, west, north, east = map(float, bbox_str.split(','))
    return (north - south) * (east - west)

def split_bbox_into_tiles(bbox_str: str, max_tiles: int = 16) -> List[str]:
    """Split a large bounding box into smaller tiles"""
    south, west, north, east = map(float, bbox_str.split(','))
    
    # Calculate how many tiles we need in each direction
    area = (north - south) * (east - west)
    if area <= 1.0:  # If area is small enough, don't split
        return [bbox_str]
    
    # Calculate optimal grid size (try to keep tiles roughly square)
    lat_range = north - south
    lon_range = east - west
    
    # Start with a 2x2 grid and increase if needed
    grid_size = 2
    while grid_size * grid_size < max_tiles and area / (grid_size * grid_size) > 1.0:
        grid_size += 1
    
    # Create tiles
    tiles = []
    lat_step = lat_range / grid_size
    lon_step = lon_range / grid_size
    
    for i in range(grid_size):
        for j in range(grid_size):
            tile_south = south + i * lat_step
            tile_north = south + (i + 1) * lat_step
            tile_west = west + j * lon_step
            tile_east = west + (j + 1) * lon_step
            
            tile_bbox = f"{tile_south},{tile_west},{tile_north},{tile_east}"
            tiles.append(tile_bbox)
    
    return tiles

def query_overpass(query: str) -> dict:
    """Execute an Overpass API query"""
    try:
        response = requests.get(OVERPASS_URL, params={'data': query}, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print_error(f"Error querying Overpass API: {e}")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Error parsing JSON response: {e}")
        return None

def generate_broad_overpass_query(bbox: str, place_types: Optional[List[str]] = None, timeout: int = 60) -> str:
    """Generate Overpass API query to get all named places (for fuzzy matching)"""
    
    # Base query parts for all named elements
    queries = []
    
    # Add place type filters if specified
    if place_types:
        for place_type in place_types:
            if '=' in place_type:
                # Handle key=value format (e.g., "amenity=restaurant")
                key, value = place_type.split('=', 1)
                type_filter = f'["{key}"="{value}"]'
            else:
                # Handle key-only format (e.g., "amenity")
                type_filter = f'["{place_type}"]'
            
            queries.extend([
                f'node["name"]{type_filter}({bbox});',
                f'way["name"]{type_filter}({bbox});',
                f'relation["name"]{type_filter}({bbox});'
            ])
    else:
        # No place type filter - search all named elements
        queries.extend([
            f'node["name"]({bbox});',
            f'way["name"]({bbox});',
            f'relation["name"]({bbox});'
        ])
    
    query = f"""
    [out:json][timeout:{timeout}];
    (
      {chr(10).join('  ' + q for q in queries)}
    );
    out center meta;
    """
    
    return query

def query_overpass_with_chunking(search_term: str, bbox: str, place_types: Optional[List[str]] = None, 
                                exact_match: bool = False, timeout: int = 60, broad_search: bool = False) -> dict:
    """Execute Overpass API query with automatic chunking for large areas"""
    
    area = calculate_bbox_area(bbox)
    print_info(f"Bounding box area: {Fore.YELLOW}{area:.2f}{Style.RESET_ALL} square degrees")
    
    # If area is small enough, use single query
    if area <= 1.0:
        print_info("Area is small enough for single query")
        if broad_search:
            query = generate_broad_overpass_query(bbox, place_types, timeout)
        else:
            query = generate_overpass_query(search_term, bbox, place_types, exact_match, timeout)
        return query_overpass(query)
    
    # Split into smaller tiles
    print_warning(f"Large area detected! Splitting into smaller tiles to avoid timeout...")
    tiles = split_bbox_into_tiles(bbox)
    print_info(f"Split into {Fore.YELLOW}{len(tiles)}{Style.RESET_ALL} tiles for processing")
    
    # Execute queries on each tile
    all_elements = []
    successful_tiles = 0
    
    for i, tile_bbox in enumerate(tiles, 1):
        print_info(f"Processing tile {Fore.CYAN}{i}/{len(tiles)}{Style.RESET_ALL}...")
        
        if broad_search:
            query = generate_broad_overpass_query(tile_bbox, place_types, timeout)
        else:
            query = generate_overpass_query(search_term, tile_bbox, place_types, exact_match, timeout)
        
        result = query_overpass(query)
        
        if result and 'elements' in result:
            tile_elements = result['elements']
            all_elements.extend(tile_elements)
            successful_tiles += 1
            print_success(f"Tile {i}: Found {Fore.YELLOW}{len(tile_elements)}{Style.RESET_ALL} elements")
        else:
            print_warning(f"Tile {i}: No data or query failed")
        
        # Small delay between requests to be nice to the API
        time.sleep(0.5)
    
    print_success(f"Completed {Fore.YELLOW}{successful_tiles}/{len(tiles)}{Style.RESET_ALL} tiles successfully")
    
    # Deduplicate results (same OSM ID)
    seen_ids = set()
    unique_elements = []
    
    for element in all_elements:
        element_id = f"{element['type']}{element['id']}"
        if element_id not in seen_ids:
            seen_ids.add(element_id)
            unique_elements.append(element)
    
    if len(all_elements) != len(unique_elements):
        print_info(f"Removed {Fore.YELLOW}{len(all_elements) - len(unique_elements)}{Style.RESET_ALL} duplicate entries")
    
    # Return in the same format as single query
    return {
        'elements': unique_elements,
        'generator': 'place_detective_chunked'
    }

def generate_overpass_query(search_term: str, bbox: str, place_types: Optional[List[str]] = None,
                           exact_match: bool = False, timeout: int = 60) -> str:
    """Generate Overpass API query with optional place type filtering"""

    # Create search pattern
    if exact_match:
        pattern = f'"name"="{search_term}"'
    else:
        # Case-insensitive regex for variations
        escaped_term = re.escape(search_term)
        pattern = f'"name"~".*{escaped_term}.*",i'

    # Base query parts
    queries = []

    # Add place type filters if specified
    if place_types:
        for place_type in place_types:
            if '=' in place_type:
                # Handle key=value format (e.g., "amenity=restaurant")
                key, value = place_type.split('=', 1)
                type_filter = f'["{key}"="{value}"]'
            else:
                # Handle key-only format (e.g., "amenity")
                type_filter = f'["{place_type}"]'

            queries.extend([
                f'node[{pattern}]{type_filter}({bbox});',
                f'way[{pattern}]{type_filter}({bbox});',
                f'relation[{pattern}]{type_filter}({bbox});'
            ])
    else:
        # No place type filter - search all named elements
        queries.extend([
            f'node[{pattern}]({bbox});',
            f'way[{pattern}]({bbox});',
            f'relation[{pattern}]({bbox});'
        ])

    query = f"""
    [out:json][timeout:{timeout}];
    (
      {chr(10).join('  ' + q for q in queries)}
    );
    out center meta;
    """

    return query

def extract_place_info(elements: List[dict]) -> List[dict]:
    """Extract relevant information from OSM elements"""
    places = []

    for element in elements:
        if 'tags' in element and 'name' in element['tags']:
            name = element['tags']['name']
            tags = element.get('tags', {})

            # Get coordinates
            if element['type'] == 'node':
                lat, lon = element['lat'], element['lon']
            elif 'center' in element:
                lat, lon = element['center']['lat'], element['center']['lon']
            else:
                lat, lon = None, None

            # Determine place category
            place_category = "unknown"
            place_subcategory = "unknown"

            for key, value in tags.items():
                if key in ['amenity', 'shop', 'leisure', 'tourism', 'healthcare', 'education']:
                    place_category = key
                    place_subcategory = value
                    break

            # Extract additional useful information
            address_parts = []
            if 'addr:housenumber' in tags:
                address_parts.append(tags['addr:housenumber'])
            if 'addr:street' in tags:
                address_parts.append(tags['addr:street'])
            if 'addr:district' in tags:
                address_parts.append(tags['addr:district'])
            if 'addr:city' in tags:
                address_parts.append(tags['addr:city'])

            address = ', '.join(address_parts) if address_parts else None

            place_info = {
                'name': name,
                'type': element['type'],
                'id': element['id'],
                'lat': lat,
                'lon': lon,
                'category': place_category,
                'subcategory': place_subcategory,
                'address': address,
                'phone': tags.get('phone', None),
                'website': tags.get('website', None),
                'opening_hours': tags.get('opening_hours', None),
                'brand': tags.get('brand', None),
                'cuisine': tags.get('cuisine', None),
                'tags': tags
            }
            places.append(place_info)

    return places

def format_place_details(place: dict, index: int = None) -> str:
    """Format place details for detective case file display with colors"""
    details = []

    # Place name with index
    if index is not None:
        details.append(f"{Fore.CYAN}{Style.BRIGHT}🏢 [{index}] {place['name']}{Style.RESET_ALL}")
    else:
        details.append(f"{Fore.CYAN}{Style.BRIGHT}🏢 {place['name']}{Style.RESET_ALL}")

    # Basic case info with colors
    details.append(f"    {Fore.BLUE}🔍 Type:{Style.RESET_ALL} {place['type']} | {Fore.BLUE}Category:{Style.RESET_ALL} {Fore.YELLOW}{place['category']}/{place['subcategory']}{Style.RESET_ALL}")
    details.append(f"    {Fore.BLUE}🆔 OSM ID:{Style.RESET_ALL} {place['id']}")
    details.append(f"    {Fore.GREEN}📍 Location:{Style.RESET_ALL} {Fore.MAGENTA}{place['lat']}, {place['lon']}{Style.RESET_ALL}")

    # Additional evidence if available with colors and emojis
    if place['address']:
        details.append(f"    {Fore.BLUE}🏠 Address:{Style.RESET_ALL} {place['address']}")
    if place['phone']:
        details.append(f"    {Fore.BLUE}📞 Phone:{Style.RESET_ALL} {place['phone']}")
    if place['website']:
        details.append(f"    {Fore.BLUE}🌐 Website:{Style.RESET_ALL} {Fore.CYAN}{place['website']}{Style.RESET_ALL}")
    if place['opening_hours']:
        details.append(f"    {Fore.BLUE}🕐 Hours:{Style.RESET_ALL} {place['opening_hours']}")
    if place['brand']:
        details.append(f"    {Fore.BLUE}🏷️  Brand:{Style.RESET_ALL} {Fore.YELLOW}{place['brand']}{Style.RESET_ALL}")
    if place['cuisine']:
        details.append(f"    {Fore.BLUE}🍽️  Cuisine:{Style.RESET_ALL} {place['cuisine']}")

    # Investigation link with special formatting
    if place['lat'] and place['lon']:
        details.append(f"    {Fore.GREEN}🗺️  Maps:{Style.RESET_ALL} {Fore.UNDERLINE}{Fore.CYAN}https://www.google.com/maps?q={place['lat']},{place['lon']}{Style.RESET_ALL}")

    return '\n'.join(details)

def find_similar_names(target_name: str, all_names: List[str], threshold: int = 80) -> List[Tuple[str, int]]:
    """Find names similar to target using improved fuzzy matching"""
    similar_names = []
    target_lower = target_name.lower()
    min_length = max(3, len(target_name) // 3)  # Minimum length is 3 or 1/3 of target length

    for name in all_names:
        # Skip very short names that could cause false positives
        if len(name) < min_length:
            continue

        name_lower = name.lower()

        # Skip if the name is too different in length
        if abs(len(name_lower) - len(target_lower)) > len(target_lower):
            continue

        # Use multiple similarity algorithms and take the best score
        ratio_score = fuzz.ratio(target_lower, name_lower)
        token_sort_score = fuzz.token_sort_ratio(target_lower, name_lower)
        token_set_score = fuzz.token_set_ratio(target_lower, name_lower)

        # Take the maximum score from different algorithms
        similarity = max(ratio_score, token_sort_score, token_set_score)

        # Only include if similarity is above threshold
        if similarity >= threshold:
            similar_names.append((name, similarity))

    return sorted(similar_names, key=lambda x: x[1], reverse=True)

def analyze_findings(places: List[dict]) -> dict:
    """Analyze the investigation findings"""
    analysis = {
        'total_places': len(places),
        'unique_names': len(set(place['name'] for place in places)),
        'multiple_locations': {},
        'name_variations': []
    }

    # Group by exact name
    name_groups = {}
    for place in places:
        name = place['name']
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(place)

    # Find names with multiple locations
    for name, group in name_groups.items():
        if len(group) > 1:
            analysis['multiple_locations'][name] = group

    # Find name variations using fuzzy matching
    names = list(name_groups.keys())
    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            similarity = fuzz.ratio(name1.lower(), name2.lower())
            if similarity > 80:  # High similarity threshold
                analysis['name_variations'].append({
                    'name1': name1,
                    'name2': name2,
                    'similarity': similarity,
                    'places1': name_groups[name1],
                    'places2': name_groups[name2]
                })

    return analysis

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="🕵️ Place Detective - Find and investigate places in OpenStreetMap data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔍 INVESTIGATION EXAMPLES:
  # Investigate McDonald's restaurants in Bangkok
  python place_detective.py -s "McDonald" -c bangkok -t amenity=restaurant

  # Track down 7-Eleven stores across Thailand
  python place_detective.py -s "7-Eleven" -c thailand -t shop=convenience

  # Search for Starbucks cafes with exact matching
  python place_detective.py -s "Starbucks" -c bangkok -t amenity=cafe --exact

  # Investigate Central shopping centers
  python place_detective.py -s "Central" -c bangkok -t shop=mall

  # Search for hospitals with "Bangkok" in name
  python place_detective.py -s "Bangkok" -c thailand -t amenity=hospital

  # Find all amenities with fuzzy matching disabled
  python place_detective.py -s "Lotus" -c thailand -t amenity --no-fuzzy

  # Output as JSON file for data analysis
  python place_detective.py -s "Big C" -c bangkok --output json

  # Export to CSV file for case file analysis
  python place_detective.py -s "Family Mart" -c thailand --output csv

  # Specify custom output filename
  python place_detective.py -s "Rimping" -c chiangmai --output csv -o "rimping_stores.csv"

🔍 DETECTIVE FEATURES:
  ✅ Detailed place investigation with GPS coordinates
  ✅ Google Maps links for instant location verification
  ✅ Contact info: address, phone, website, hours
  ✅ Brand and cuisine information (when available)
  ✅ Advanced place finding with similarity scoring
  ✅ Multiple output formats (table, JSON file, CSV file)
  ✅ Auto-generated filenames with timestamps

🌍 INVESTIGATION AREAS: bangkok, chiangmai, phuket, pattaya, chiangrai, hatyai, korat, thailand
🏷️  PLACE TYPES: amenity, shop, leisure, tourism, healthcare, education
    Or specific: amenity=restaurant, shop=supermarket, tourism=hotel, etc.
        """
    )

    parser.add_argument('-s', '--search', required=True,
                       help='Search term (e.g., "McDonald", "7-Eleven", "Starbucks")')
    parser.add_argument('-c', '--city', choices=list(CITY_BBOXES.keys()), default='bangkok',
                       help='City/region to search in (default: bangkok)')
    parser.add_argument('--area-scope', choices=['city', 'province'], default='city',
                       help='Search scope: city (fast, focused) or province (comprehensive, slower) (default: city)')
    parser.add_argument('-t', '--types', nargs='*',
                       help='Place types to filter (e.g., amenity, shop, amenity=restaurant)')
    parser.add_argument('--exact', action='store_true',
                       help='Use exact name matching instead of partial matching')
    parser.add_argument('--no-fuzzy', action='store_true',
                       help='Disable fuzzy matching')
    parser.add_argument('--fuzzy-threshold', type=int, default=85,
                       help='Fuzzy matching threshold (default: 85)')
    parser.add_argument('--timeout', type=int, default=60,
                       help='Query timeout in seconds (default: 60)')
    parser.add_argument('--output', choices=['table', 'json', 'csv'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('-o', '--output-file',
                       help='Output file path (optional, defaults to auto-generated filename)')

    return parser.parse_args()

def main():
    """Main function to execute the place investigation"""
    args = parse_arguments()

    # Colorful header
    print()
    print_header("🕵️ PLACE DETECTIVE - INVESTIGATION REPORT 🕵️")
    print()
    print_detective(f"Investigating '{Fore.YELLOW}{args.search}{Style.RESET_ALL}' in {Fore.CYAN}{args.city.title()}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'=' * 70}{Style.RESET_ALL}")

    # Install packages if needed
    if not install_packages():
        return

    # Get configuration
    # Select bounding box based on area scope
    if args.area_scope == 'province':
        bbox = PROVINCE_BBOXES[args.city]
        scope_description = f"province (comprehensive coverage)"
    else:
        bbox = CITY_BBOXES[args.city]
        scope_description = f"city (focused coverage)"
    
    search_term = args.search
    place_types = args.types

    # Display search parameters with colors
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}🔧 INVESTIGATION PARAMETERS:{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}🔍 Search term:{Style.RESET_ALL} '{Fore.YELLOW}{search_term}{Style.RESET_ALL}'")
    print(f"  {Fore.BLUE}🌍 Area:{Style.RESET_ALL} {Fore.CYAN}{args.city.title()}{Style.RESET_ALL} ({Fore.MAGENTA}{scope_description}{Style.RESET_ALL})")
    print(f"  {Fore.BLUE}🏷️  Place types:{Style.RESET_ALL} {Fore.GREEN}{place_types if place_types else 'All types'}{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}🎯 Exact match:{Style.RESET_ALL} {Fore.YELLOW}{args.exact}{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}🔄 Fuzzy matching:{Style.RESET_ALL} {Fore.YELLOW}{not args.no_fuzzy}{Style.RESET_ALL}")

    # Generate and execute query
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}🔍 STEP 1: Investigating '{Fore.YELLOW}{search_term}{Style.RESET_ALL}{Fore.MAGENTA}{Style.BRIGHT}'...{Style.RESET_ALL}")
    result = query_overpass_with_chunking(
        search_term=search_term,
        bbox=bbox,
        place_types=place_types,
        exact_match=args.exact,
        timeout=args.timeout
    )

    if result:
        print_info(f"Found {Fore.YELLOW}{len(result.get('elements', []))}{Style.RESET_ALL} elements from OSM database")
        places = extract_place_info(result['elements'])

        if places:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 INVESTIGATION RESULTS:{Style.RESET_ALL}")
            print_success(f"Found {Fore.YELLOW}{len(places)}{Style.RESET_ALL} places matching '{Fore.YELLOW}{search_term}{Style.RESET_ALL}'")
            print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

            # Handle output format
            if args.output == 'table':
                # Display to terminal with colors
                print()
                for i, place in enumerate(places, 1):
                    print(format_place_details(place, i))
                    if i < len(places):
                        print()

            elif args.output == 'json':
                # Generate filename if not provided
                if args.output_file:
                    filename = args.output_file
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_search_term = re.sub(r'[^\w\-_]', '_', search_term)
                    filename = f"place_detective_{safe_search_term}_{args.city}_{timestamp}.json"

                # Remove internal tags for cleaner JSON output
                clean_places = []
                for place in places:
                    clean_place = {k: v for k, v in place.items() if k != 'tags'}
                    clean_places.append(clean_place)

                # Write to file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(clean_places, f, indent=2, ensure_ascii=False)

                print_file(f"JSON report saved to: {Fore.CYAN}{filename}{Style.RESET_ALL}")

            elif args.output == 'csv':
                # Generate filename if not provided
                if args.output_file:
                    filename = args.output_file
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_search_term = re.sub(r'[^\w\-_]', '_', search_term)
                    filename = f"place_detective_{safe_search_term}_{args.city}_{timestamp}.csv"

                # Prepare CSV data
                df = pd.DataFrame(places)
                display_columns = ['name', 'type', 'id', 'lat', 'lon', 'category', 'subcategory',
                                 'address', 'phone', 'website', 'opening_hours', 'brand', 'cuisine']
                available_columns = [col for col in display_columns if col in df.columns]

                # Write to file
                df[available_columns].to_csv(filename, index=False)
                print_file(f"CSV report saved to: {Fore.CYAN}{filename}{Style.RESET_ALL}")
        else:
            print_warning("No places found with specified criteria")
    else:
        print_error("Query failed")
        places = []

    # Analyze findings if we found places
    if places:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}🕵️ STEP 2: Analyzing investigation findings...{Style.RESET_ALL}")
        analysis = analyze_findings(places)

        print_info(f"Total places found: {Fore.YELLOW}{analysis['total_places']}{Style.RESET_ALL}")
        print_info(f"Unique names: {Fore.YELLOW}{analysis['unique_names']}{Style.RESET_ALL}")

        if analysis['multiple_locations']:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}📍 MULTIPLE LOCATIONS DISCOVERED{Style.RESET_ALL}")
            for name, locations in analysis['multiple_locations'].items():
                print(f"\n{Fore.YELLOW}{Style.BRIGHT}🏢 '{name}' found at {len(locations)} locations:{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'-' * 50}{Style.RESET_ALL}")
                for i, place in enumerate(locations, 1):
                    print(format_place_details(place, i))
                    if i < len(locations):
                        print()
        else:
            print_success("Each place name found at single location")

        if analysis['name_variations']:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}🔍 SIMILAR NAME VARIATIONS DISCOVERED{Style.RESET_ALL}")
            for variation in analysis['name_variations']:
                print(f"\n{Fore.MAGENTA}🔍 '{variation['name1']}' vs '{variation['name2']}' (similarity: {Fore.YELLOW}{variation['similarity']}%{Fore.MAGENTA}){Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}{Style.BRIGHT}First variation:{Style.RESET_ALL}")
                for i, place in enumerate(variation['places1'], 1):
                    print(format_place_details(place, f"A{i}"))
                    if i < len(variation['places1']):
                        print()
                print(f"\n{Fore.BLUE}{Style.BRIGHT}Second variation:{Style.RESET_ALL}")
                for i, place in enumerate(variation['places2'], 1):
                    print(format_place_details(place, f"B{i}"))
                    if i < len(variation['places2']):
                        print()
        else:
            print_info("No similar name variations found")

    # Optional fuzzy matching for broader search
    if not args.no_fuzzy and places:
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}🔍 STEP 3: Expanding search with fuzzy matching...{Style.RESET_ALL}")

        # Get all places in the area for comparison
        print_info("Gathering all places from the area (this may take a while)...")

        # Create a broader query to get all named places
        if place_types:
            type_filters = []
            for place_type in place_types:
                if '=' in place_type:
                    key, value = place_type.split('=', 1)
                    type_filters.append(f'["{key}"="{value}"]')
                else:
                    type_filters.append(f'["{place_type}"]')

            queries = []
            for type_filter in type_filters:
                queries.extend([
                    f'node["name"]{type_filter}({bbox});',
                    f'way["name"]{type_filter}({bbox});',
                    f'relation["name"]{type_filter}({bbox});'
                ])
        else:
            queries = [
                f'node["name"]({bbox});',
                f'way["name"]({bbox});',
                f'relation["name"]({bbox});'
            ]

        print_info("Using chunking system for fuzzy matching broad search...")
        
        # Use chunking for fuzzy matching broad search
        broad_result = query_overpass_with_chunking(
            search_term="",  # Not used for broad search
            bbox=bbox,
            place_types=place_types,
            exact_match=False,
            timeout=args.timeout,
            broad_search=True
        )

        if broad_result:
            all_places = extract_place_info(broad_result['elements'])
            all_names = [place['name'] for place in all_places]

            similar_names = find_similar_names(search_term, all_names, threshold=args.fuzzy_threshold)

            if similar_names:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}🔍 ADDITIONAL FINDINGS - Similar Places to '{Fore.YELLOW}{search_term}{Style.RESET_ALL}{Fore.CYAN}{Style.BRIGHT}':{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")

                # Get detailed info for fuzzy matches
                fuzzy_places = []
                for name, score in similar_names[:10]:  # Show top 10 matches
                    matching_places = [p for p in all_places if p['name'] == name]
                    if matching_places:
                        fuzzy_places.append((matching_places[0], score))

                print()
                for i, (place, score) in enumerate(fuzzy_places, 1):
                    print(f"{Fore.CYAN}{Style.BRIGHT}🏢 [{i}] {place['name']} (similarity: {Fore.YELLOW}{score}%{Fore.CYAN}){Style.RESET_ALL}")
                    print(f"    {Fore.BLUE}🔍 Type:{Style.RESET_ALL} {place['type']} | {Fore.BLUE}Category:{Style.RESET_ALL} {Fore.YELLOW}{place['category']}/{place['subcategory']}{Style.RESET_ALL}")
                    print(f"    {Fore.BLUE}🆔 OSM ID:{Style.RESET_ALL} {place['id']}")
                    print(f"    {Fore.GREEN}📍 Location:{Style.RESET_ALL} {Fore.MAGENTA}{place['lat']}, {place['lon']}{Style.RESET_ALL}")
                    if place['address']:
                        print(f"    {Fore.BLUE}🏠 Address:{Style.RESET_ALL} {place['address']}")
                    if place['brand']:
                        print(f"    {Fore.BLUE}🏷️  Brand:{Style.RESET_ALL} {Fore.YELLOW}{place['brand']}{Style.RESET_ALL}")
                    if place['lat'] and place['lon']:
                        print(f"    {Fore.GREEN}🗺️  Maps:{Style.RESET_ALL} {Fore.UNDERLINE}{Fore.CYAN}https://www.google.com/maps?q={place['lat']},{place['lon']}{Style.RESET_ALL}")
                    if i < len(fuzzy_places):
                        print()
            else:
                print_info(f"No similar places found for '{search_term}'")
        else:
            print_error("Failed to fetch data for fuzzy matching")

    # Summary
    print(f"\n{Fore.BLUE}{'='*70}{Style.RESET_ALL}")
    print_header("🕵️ FINAL INVESTIGATION SUMMARY 🕵️")
    print(f"{Fore.BLUE}{'='*70}{Style.RESET_ALL}")

    if 'analysis' in locals():
        if analysis['multiple_locations']:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}📍 MULTIPLE LOCATIONS DISCOVERED{Style.RESET_ALL}")
            for name, locations in analysis['multiple_locations'].items():
                print(f"  {Fore.YELLOW}• '{name}' found at {len(locations)} locations{Style.RESET_ALL}")
                print(f"    {Fore.BLUE}🔍 Investigation notes:{Style.RESET_ALL}")
                print(f"    {Fore.GREEN}   - Same business name at different locations{Style.RESET_ALL}")
                print(f"    {Fore.GREEN}   - Could be chain locations or branches{Style.RESET_ALL}")
                print(f"    {Fore.GREEN}   - Different OSM element types possible{Style.RESET_ALL}")

        if analysis['name_variations']:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}🔍 NAME VARIATIONS DISCOVERED{Style.RESET_ALL}")
            for variation in analysis['name_variations']:
                print(f"  {Fore.MAGENTA}• '{variation['name1']}' vs '{variation['name2']}' ({variation['similarity']}% similar){Style.RESET_ALL}")
                print(f"    {Fore.BLUE}🔍 Investigation notes:{Style.RESET_ALL}")
                print(f"    {Fore.GREEN}   - Similar names that might be related{Style.RESET_ALL}")
                print(f"    {Fore.GREEN}   - Could be different spellings or translations{Style.RESET_ALL}")

        if not analysis['multiple_locations'] and not analysis['name_variations']:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ INVESTIGATION COMPLETE{Style.RESET_ALL}")
            print(f"  {Fore.BLUE}🔍 Investigation results for '{Fore.YELLOW}{search_term}{Style.RESET_ALL}{Fore.BLUE}':{Style.RESET_ALL}")
            if analysis['total_places'] > 0:
                print(f"  {Fore.GREEN}✅ Found {Fore.YELLOW}{analysis['total_places']}{Style.RESET_ALL}{Fore.GREEN} unique place(s) matching the criteria{Style.RESET_ALL}")
                print(f"  {Fore.GREEN}✅ Each place has a unique name and location{Style.RESET_ALL}")
            else:
                print(f"  {Fore.YELLOW}⚠️  No places found matching '{search_term}'{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}{Style.BRIGHT}❌ INVESTIGATION INCOMPLETE{Style.RESET_ALL}")
        print(f"  {Fore.RED}Unable to complete the investigation due to data retrieval issues{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Try running the detective work again or check your internet connection{Style.RESET_ALL}")

    print(f"\n{Fore.BLUE}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}🕵️ Investigation completed! Detective work finished. 🔍{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Thank you for using Place Detective! 🎉{Style.RESET_ALL}")
    print()

if __name__ == "__main__":
    main()