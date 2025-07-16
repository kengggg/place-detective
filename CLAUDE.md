# Place Detective - OpenStreetMap Investigation Tool

## Overview
Place Detective is a comprehensive Python tool for investigating places in OpenStreetMap data. It acts as a "detective" to find suspicious place patterns, similar spellings, and potential data inconsistencies across different cities and regions, with a focus on Thai geographic areas.

## Key Features

### 🔍 Search Capabilities
- **Exact Match Search**: Find places with exact name matching
- **Fuzzy Matching**: Use advanced algorithms to find similar names with configurable similarity thresholds
- **Pattern Matching**: Case-insensitive regex search for name variations
- **Type Filtering**: Filter by specific place types (restaurants, shops, hotels, etc.)

### 🌍 Geographic Coverage
- **Thai Focus**: Pre-configured for Bangkok, Chiang Mai, Phuket, Pattaya, Chiang Rai, Hat Yai, Korat, and all of Thailand
- **Dual Scope**: City-level (fast, focused) and province-level (comprehensive, slower) searches
- **Smart Chunking**: Automatically splits large areas into smaller tiles to avoid API timeouts
- **Bounding Box Management**: Optimized coordinate boundaries for efficient queries

### 📊 Data Analysis
- **Duplicate Detection**: Identifies businesses with multiple locations (chain analysis)
- **Name Variations**: Finds similar names that might be typos, alternate spellings, or translations
- **Place Information**: Extracts detailed data including coordinates, addresses, contact info, hours, brands
- **Similarity Scoring**: Advanced fuzzy matching with multiple algorithms (ratio, token sort, token set)

### 🎨 Output Options
- **Colorful Console**: Rich terminal display with emojis and color coding
- **JSON Export**: Machine-readable format for programmatic analysis
- **CSV Export**: Spreadsheet-compatible format for data analysis
- **Auto-generated Filenames**: Timestamped files with safe naming conventions

## Installation & Dependencies

### Required Packages
```bash
pip install requests pandas fuzzywuzzy[speedup] colorama
```

### Optional Dependencies
- `colorama`: For colored terminal output (fallback to plain text if not available)
- `python-Levenshtein`: For faster fuzzy matching (included in fuzzywuzzy[speedup])

## Usage Examples

### Basic Search
```bash
# Search for McDonald's in Bangkok
python place_detective.py -s "McDonald" -c bangkok

# Find 7-Eleven stores across Thailand
python place_detective.py -s "7-Eleven" -c thailand -t shop=convenience

# Search for Starbucks cafes with exact matching
python place_detective.py -s "Starbucks" -c bangkok -t amenity=cafe --exact
```

### Advanced Filtering
```bash
# Search for hospitals with "Bangkok" in name
python place_detective.py -s "Bangkok" -c thailand -t amenity=hospital

# Find Central shopping centers
python place_detective.py -s "Central" -c bangkok -t shop=mall

# Search all amenities with fuzzy matching disabled
python place_detective.py -s "Lotus" -c thailand -t amenity --no-fuzzy
```

### Output Formats
```bash
# Export to JSON
python place_detective.py -s "Big C" -c bangkok --output json

# Export to CSV
python place_detective.py -s "Family Mart" -c thailand --output csv

# Custom output filename
python place_detective.py -s "Rimping" -c chiangmai --output csv -o "rimping_stores.csv"
```

### Search Scope Options
```bash
# City-level search (fast, focused)
python place_detective.py -s "Tesco" -c bangkok --area-scope city

# Province-level search (comprehensive, slower)
python place_detective.py -s "Tesco" -c bangkok --area-scope province
```

## Command Line Arguments

### Required Arguments
- `-s, --search`: Search term (e.g., "McDonald", "7-Eleven", "Starbucks")

### Optional Arguments
- `-c, --city`: City/region to search (default: bangkok)
  - Options: bangkok, chiangmai, phuket, pattaya, chiangrai, hatyai, korat, thailand
- `--area-scope`: Search scope - city (fast) or province (comprehensive) (default: city)
- `-t, --types`: Place types to filter (e.g., amenity, shop, amenity=restaurant)
- `--exact`: Use exact name matching instead of partial matching
- `--no-fuzzy`: Disable fuzzy matching for additional findings
- `--fuzzy-threshold`: Fuzzy matching similarity threshold (default: 85)
- `--timeout`: Query timeout in seconds (default: 60)
- `--output`: Output format - table, json, csv (default: table)
- `-o, --output-file`: Custom output file path

## Place Types

### Supported Categories
- **amenity**: restaurant, cafe, bar, hospital, school, bank, hotel, shop
- **shop**: supermarket, convenience, mall, department_store, bakery, butcher
- **leisure**: park, garden, sports_centre, fitness_centre, swimming_pool
- **tourism**: hotel, guest_house, attraction, museum, viewpoint
- **healthcare**: hospital, clinic, pharmacy, dentist, veterinary
- **education**: school, university, college, kindergarten, library

### Filter Examples
```bash
# General category
-t amenity

# Specific type
-t amenity=restaurant

# Multiple types
-t amenity=restaurant shop=convenience tourism=hotel
```

## Geographic Areas

### City-level Bounding Boxes (Fast, Focused)
- **Bangkok**: Greater Bangkok Metropolitan Area
- **Chiang Mai**: Chiang Mai city and key districts
- **Phuket**: Phuket Island complete coverage
- **Pattaya**: Pattaya-Chonburi coastal region
- **Chiang Rai**: Chiang Rai city and surrounding area
- **Hat Yai**: Hat Yai city in Songkhla province
- **Korat**: Nakhon Ratchasima (Korat) city
- **Thailand**: Complete country boundaries

### Province-level Bounding Boxes (Comprehensive, Slower)
- Extended coverage for each region including surrounding provinces
- Automatically uses chunking system for large areas
- Suitable for comprehensive business analysis

## Technical Features

### Smart Chunking System
- Automatically detects large search areas (>1 square degree)
- Splits into optimal grid tiles to avoid API timeouts
- Deduplicates results across tiles
- Progress tracking for multi-tile operations

### Fuzzy Matching Algorithms
- **Ratio**: Simple character-by-character comparison
- **Token Sort**: Compares sorted word tokens
- **Token Set**: Handles different word orders
- **Configurable Threshold**: Adjustable similarity requirements

### Data Extraction
- **Coordinates**: Latitude/longitude for mapping
- **Address**: Structured address components
- **Contact Info**: Phone, website, opening hours
- **Business Info**: Brand, cuisine type, category
- **OSM Metadata**: Element type, ID, tags

## Investigation Process

### Step 1: Primary Search
1. Execute search query with specified parameters
2. Handle large areas with automatic chunking
3. Extract and format place information
4. Display results with detailed information

### Step 2: Analysis
1. Group places by exact name matches
2. Identify multiple locations for same business
3. Find name variations using fuzzy matching
4. Generate investigation summary

### Step 3: Fuzzy Expansion (Optional)
1. Gather all places in search area
2. Compare against search term using fuzzy algorithms
3. Display additional similar places
4. Provide similarity scores

## API Integration

### Overpass API
- **Endpoint**: http://overpass-api.de/api/interpreter
- **Query Language**: Overpass QL
- **Timeout Handling**: Configurable timeout with chunking fallback
- **Rate Limiting**: Built-in delays between requests
- **Error Handling**: Comprehensive error reporting

### Query Types
- **Node Queries**: Point locations
- **Way Queries**: Linear features and building outlines
- **Relation Queries**: Complex geographic relationships
- **Combined Queries**: All element types in single request

## Output Formats

### Console Display
- **Colorful Output**: Different colors for different information types
- **Emoji Icons**: Visual indicators for different data types
- **Structured Layout**: Organized presentation of findings
- **Progress Tracking**: Real-time feedback during processing

### JSON Export
- **Clean Structure**: Removes internal tags for clarity
- **UTF-8 Encoding**: Proper handling of international characters
- **Timestamped Files**: Automatic filename generation
- **Machine Readable**: Suitable for further processing

### CSV Export
- **Spreadsheet Compatible**: Works with Excel, Google Sheets
- **Selected Columns**: Key information for analysis
- **Proper Encoding**: UTF-8 for international characters
- **Structured Data**: Consistent format for analysis

## Error Handling

### Network Issues
- **Timeout Handling**: Graceful handling of slow responses
- **Connection Errors**: Clear error messages for network problems
- **Rate Limiting**: Automatic delays to respect API limits
- **Retry Logic**: Built-in chunking for large area failures

### Data Processing
- **JSON Parsing**: Handles malformed API responses
- **Missing Data**: Graceful handling of incomplete place information
- **Unicode Support**: Proper handling of international characters
- **Memory Management**: Efficient processing of large datasets

## Performance Optimization

### Area Management
- **Bounding Box Calculation**: Efficient area computation
- **Automatic Chunking**: Optimal tile size selection
- **Progress Tracking**: Real-time processing feedback
- **Memory Efficiency**: Streaming data processing

### Query Optimization
- **Targeted Searches**: Focused queries for better performance
- **Type Filtering**: Reduced data volume through filtering
- **Chunked Processing**: Parallel tile processing capability
- **Result Deduplication**: Efficient duplicate removal

## Common Use Cases

### Business Analysis
- **Chain Detection**: Find all locations of a business chain
- **Competitor Analysis**: Identify similar businesses in area
- **Market Research**: Understand business distribution patterns
- **Location Planning**: Analyze existing business locations

### Data Quality Assessment
- **Duplicate Detection**: Find potential duplicate entries
- **Name Standardization**: Identify naming inconsistencies
- **Data Validation**: Verify business information accuracy
- **Mapping Quality**: Assess OpenStreetMap data completeness

### Geographic Research
- **Urban Planning**: Understand business distribution
- **Tourism Analysis**: Find tourist attractions and services
- **Infrastructure Assessment**: Analyze service availability
- **Cultural Mapping**: Document local businesses and places

## Troubleshooting

### Common Issues
- **No Results**: Check spelling, try broader search terms, verify area coverage
- **Timeout Errors**: Use smaller search areas or increase timeout value
- **Memory Issues**: Use chunking for large areas, reduce fuzzy threshold
- **API Errors**: Check internet connection, try again later

### Performance Tips
- **Use City Scope**: Faster than province scope for most searches
- **Specific Types**: Filter by place types for focused results
- **Exact Matching**: Faster than fuzzy matching for known names
- **Reasonable Timeouts**: Balance between thoroughness and speed

## Development Notes

### Code Structure
- **Modular Design**: Separate functions for different operations
- **Error Handling**: Comprehensive error management
- **Configuration**: Centralized settings for easy modification
- **Documentation**: Extensive inline documentation

### Extension Points
- **New Regions**: Easy addition of new geographic areas
- **Additional APIs**: Framework for other data sources
- **Output Formats**: Extensible output system
- **Analysis Methods**: Pluggable analysis algorithms

## Testing Commands

### Quick Tests
```bash
# Test basic functionality
python place_detective.py -s "McDonald" -c bangkok --exact

# Test fuzzy matching
python place_detective.py -s "MacDonald" -c bangkok --fuzzy-threshold 70

# Test export functionality
python place_detective.py -s "7-Eleven" -c bangkok --output json
```

### Performance Tests
```bash
# Test chunking with large area
python place_detective.py -s "Tesco" -c thailand --area-scope province

# Test with multiple types
python place_detective.py -s "Central" -c bangkok -t shop=mall amenity=restaurant
```

## Common Patterns

### Chain Store Analysis
```bash
# Find all 7-Eleven stores in Thailand
python place_detective.py -s "7-Eleven" -c thailand -t shop=convenience --output csv

# Analyze McDonald's distribution
python place_detective.py -s "McDonald" -c thailand -t amenity=restaurant --area-scope province
```

### Name Variation Detection
```bash
# Find variations of "Starbucks"
python place_detective.py -s "Starbucks" -c bangkok -t amenity=cafe --fuzzy-threshold 80

# Check for "Tesco" vs "Tesco Lotus"
python place_detective.py -s "Tesco" -c thailand -t shop=supermarket
```

### Data Quality Checks
```bash
# Find duplicate hospital entries
python place_detective.py -s "Hospital" -c bangkok -t amenity=hospital --no-fuzzy

# Check for naming inconsistencies
python place_detective.py -s "Central" -c bangkok --fuzzy-threshold 75
```