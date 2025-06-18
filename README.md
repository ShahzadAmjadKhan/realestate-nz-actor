# Real Estate NZ Scraper

This Apify Actor scrapes property listings from realestate.co.nz, extracting comprehensive property information including prices, features, agent details, and more.

## Features

- Scrapes multiple pages of property listings
- Extracts detailed property information including:
  - Property address and type
  - Bedrooms, bathrooms, parking spaces
  - Floor area and land area
  - Sales method and pricing
  - Agent and agency information
  - Listing dates and capital valuations
  - Primary property images
- Configurable scraping parameters
- Respectful scraping with random delays
- Built-in error handling and logging

## Input Configuration

The Actor accepts the following input parameters:

### `maxPages` (integer)
- **Default**: 3
- **Range**: 1-50
- Maximum number of pages to scrape from the property listings

### `location` (string)
- **Default**: "queenstown"
- **Options**: queenstown, auckland, wellington, christchurch, hamilton, tauranga, dunedin, palmerston-north, nelson, rotorua
- The location/city to scrape property listings from

### `minDelay` (number)
- **Default**: 1.5
- **Range**: 0.5-10 seconds
- Minimum delay between individual property page requests

### `maxDelay` (number)
- **Default**: 4.0
- **Range**: 1-15 seconds
- Maximum delay between individual property page requests

## Output

The Actor outputs property data in the following format:

```json
{
  "extractDate": "2024-01-15 14:30:25",
  "listingUrl": "https://www.realestate.co.nz/...",
  "agentNames": "John Smith & Jane Doe",
  "agencyName": "Premium Real Estate",
  "primaryImageUrl": "https://...",
  "propertyAddress": "123 Lake View Drive, Queenstown",
  "salesMethod": "Auction",
  "propertyType": "House",
  "bedrooms": "4",
  "bathrooms": "2",
  "parkingSpace": "2",
  "floorArea": "180m²",
  "landArea": "650m²",
  "listingDate": "Listed 5 days ago",
  "capitalValue": "$850,000"
}
```

## Usage Tips

1. **Start Small**: Begin with a low `maxPages` value (1-3) to test the Actor
2. **Respect Rate Limits**: Use appropriate delays (1.5-4 seconds) to avoid overwhelming the target website
3. **Monitor Performance**: Larger scraping jobs may require increased memory allocation
4. **Location Specific**: Ensure the location parameter matches available regions on realestate.co.nz

## Technical Details

- **Language**: Python 3.11
- **Browser**: Chromium (Playwright)
- **Parsing**: BeautifulSoup4
- **Memory**: Recommended 2GB for larger scraping jobs
- **Timeout**: Default 1 hour (configurable)

## Compliance

This Actor is designed to scrape publicly available property listings in a respectful manner with built-in delays and error handling. Users should ensure compliance with realestate.co.nz's terms of service and applicable data protection regulations.

## Support

For questions or issues, please refer to the Apify documentation or contact support through the Apify platform.