# 🕵️ Place Detective

**Advanced place investigation tool for OpenStreetMap data**

A powerful Python detective tool to find and investigate places by name, discover multiple locations, and identify name variations in OpenStreetMap across different cities and regions.

## 🚀 Detective Features

- **🔍 Advanced Investigation**: Investigate places by name with fuzzy matching capabilities
- **🌍 Multi-City Coverage**: Investigate across Bangkok, Chiang Mai, Phuket, Pattaya, or all of Thailand
- **⚡ Dual Search Scope**: Choose between city-level (fast) or province-level (comprehensive) coverage
- **🏷️ Place Type Filtering**: Filter by amenities, shops, tourism, healthcare, education, etc.
- **📍 Detailed Evidence**: Get GPS coordinates, addresses, contact info, and more
- **🕵️ Location Discovery**: Find places with multiple locations and name variations
- **🗺️ Google Maps Integration**: Direct links to locations for easy verification
- **📊 Multiple Report Formats**: Table, JSON, and CSV case file export options
- **🎨 Colorful Terminal Output**: Rich, colorful interface with emojis and visual indicators
- **🧩 Smart Chunking**: Automatically splits large areas into smaller tiles to avoid timeouts

## 📋 Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🔍 Investigation Examples

### Basic Investigations
```bash
# Investigate McDonald's restaurants in Bangkok
python place_detective.py -s "McDonald" -c bangkok -t amenity=restaurant

# Track down 7-Eleven stores across Thailand
python place_detective.py -s "7-Eleven" -c thailand -t shop=convenience

# Search for Starbucks cafes with exact matching
python place_detective.py -s "Starbucks" -c bangkok -t amenity=cafe --exact
```

### Advanced Investigations
```bash
# Investigate Central shopping centers
python place_detective.py -s "Central" -c bangkok -t shop=mall

# Search for hospitals with "Bangkok" in name
python place_detective.py -s "Bangkok" -c thailand -t amenity=hospital

# Find all amenities with fuzzy matching disabled
python place_detective.py -s "Lotus" -c thailand -t amenity --no-fuzzy
```

### Case File Export Options
```bash
# Output as JSON file for data analysis
python place_detective.py -s "Big C" -c bangkok --output json

# Export to CSV file for case file analysis
python place_detective.py -s "Family Mart" -c thailand --output csv

# Specify custom output filename
python place_detective.py -s "Rimping" -c chiangmai --output csv -o "rimping_stores.csv"
```

### Area Scope Options
```bash
# Fast city-level search (default)
python place_detective.py -s "Central" -c chiangmai --area-scope city

# Comprehensive province-level search (slower but more thorough)
python place_detective.py -s "Central" -c chiangmai --area-scope province

# Province-wide investigation with chunking for large areas
python place_detective.py -s "7-Eleven" -c chiangmai --area-scope province --output csv
```

## 🌍 Investigation Areas

Each area supports both **city-level** (fast, focused) and **province-level** (comprehensive, slower) coverage:

- `bangkok` - Greater Bangkok Metropolitan Area / Bangkok + surrounding provinces
- `chiangmai` - Chiang Mai city and key districts / Chiang Mai province complete
- `phuket` - Phuket Island complete coverage / Phuket province + nearby islands
- `pattaya` - Pattaya-Chonburi coastal region / Chonburi province coastal area
- `chiangrai` - Chiang Rai city and surrounding area / Chiang Rai province
- `hatyai` - Hat Yai city in Songkhla province / Songkhla province southern area
- `korat` - Nakhon Ratchasima (Korat) city / Nakhon Ratchasima province
- `thailand` - Thailand complete country boundaries (same for both scopes)

## 🏷️ Place Types

**Categories:**
- `amenity` - Restaurants, cafes, hospitals, schools, etc.
- `shop` - Supermarkets, convenience stores, malls, etc.
- `leisure` - Parks, sports centers, swimming pools, etc.
- `tourism` - Hotels, attractions, museums, etc.
- `healthcare` - Hospitals, clinics, pharmacies, etc.
- `education` - Schools, universities, libraries, etc.

**Specific Types:**
- `amenity=restaurant` - Restaurants only
- `shop=supermarket` - Supermarkets only
- `tourism=hotel` - Hotels only
- And many more...

## 📊 Case File Information

For each place investigated, the detective provides:
- ✅ Place name and type
- ✅ OSM ID for reference
- ✅ GPS coordinates
- ✅ Google Maps link for verification
- ✅ Category and subcategory
- ✅ Address (if available)
- ✅ Phone number (if available)
- ✅ Website (if available)
- ✅ Opening hours (if available)
- ✅ Brand information (if available)
- ✅ Cuisine type (if available)

## 🕵️ Detective Analysis

The detective identifies:
- **Multiple locations** - Same business name at different locations
- **Name variations** - Similar names with configurable similarity threshold
- **Fuzzy matches** - Places with similar spellings or variations

## 🔍 Command Line Options

```bash
python place_detective.py -h
```

**Key Options:**
- `-s, --search` - Search term (required)
- `-c, --city` - City to search in
- `--area-scope` - Search scope: city (fast) or province (comprehensive) (default: city)
- `-t, --types` - Place types to filter
- `--exact` - Use exact name matching
- `--no-fuzzy` - Disable fuzzy matching
- `--fuzzy-threshold` - Similarity threshold (default: 85)
- `--output` - Output format (table, json, csv)
- `-o, --output-file` - Custom output filename
- `--timeout` - Query timeout in seconds

## 🧩 Smart Chunking for Large Areas

The detective automatically detects large search areas and splits them into smaller tiles to avoid API timeouts. This feature is especially useful for:

- **Large provinces** like the full Chiang Mai region
- **Country-wide searches** across Thailand
- **Complex queries** with multiple place types

When chunking is active, you'll see progress updates for each tile processed, and the results are automatically deduplicated.

## 🕵️ Happy Investigating!

Use this detective tool to find and investigate places in OpenStreetMap by discovering multiple locations and name variations. Perfect for researchers, data analysts, and OSM contributors who want to explore place data and understand location patterns!