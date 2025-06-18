import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import random
import time
from apify import Actor

BASE_URL = "https://www.realestate.co.nz"
START_URL_BASE = "https://www.realestate.co.nz/residential/sale/central-otago-lakes-district/queenstown"

# Utility to pause scrolling to allow listings to load
async def auto_scroll(page, max_retries=3, scroll_step=1000, pause_time=3):
    retries = 0
    prev_listing_count = -1
    start_time = time.time()

    while retries < max_retries:
        # Scroll a bit down (not to bottom)
        await page.mouse.wheel(0, scroll_step)
        await page.wait_for_timeout(pause_time * 1000)

        # Count current listings
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        listings = soup.select('div[data-test="tile"]')
        curr_listing_count = len(listings)

        Actor.log.info(f"Listings loaded: {curr_listing_count}")

        if curr_listing_count == prev_listing_count:
            retries += 1
        else:
            retries = 0
            prev_listing_count = curr_listing_count

    Actor.log.info("Scrolling completed.")
    return soup

# Scrape all listing URLs
def extract_listing_urls(soup):
    urls = []
    for tile in soup.select('div[data-test="tile"]'):
        anchor = tile.select_one("a:has(> div.listed-date:first-child)")
        if anchor:
            href = anchor["href"]
            full_url = BASE_URL + href if href.startswith("/") else href
            urls.append(full_url)

    return list(set(urls))  # remove duplicates

async def scrape_features(soup):
    # Find the container with the features using the data-test attribute
    container = soup.find("div", attrs={"data-test": "features-icons"})

    # Initialize an empty dictionary to store the features
    features = {}

    # If the container exists
    if container:
        # Find all divs inside the container with class 'flex items-center'
        feature_blocks = container.find_all("div", class_="flex items-center")
        for i, feature_block in enumerate(feature_blocks):
            # Extract the <title> from <svg> to identify the feature
            title_tag = feature_block.find("title")
            if title_tag:
                feature_name = title_tag.get_text(strip=True).lower().replace(" ", "_")
            else:
                feature_name = "unknown"

            # Extract the text from the <span> tag next to the icon
            feature_text = feature_block.find("span").get_text(strip=True)

            # For the first feature, use the key 'property_type'
            if i == 0:
                features['property_type'] = feature_text
            else:
                features[feature_name] = feature_text

    return features

# Scrape details from each listing page
async def scrape_details(page, url):
    await page.goto(url)
    await page.wait_for_load_state("load")
    extract_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")

    agent_names = [h3.get_text(strip=True) for h3 in soup.select('div.property-agents h3')]
    if len(agent_names) > 1:
        merged_names = ', '.join(agent_names[:-1]) + ' & ' + agent_names[-1]
    else:
        merged_names = agent_names[0] if agent_names else ''

    agency_name = soup.select_one('div[data-test="agent-info__listing-agent-office"]')
    property_address = soup.select_one('h1[data-test="listing-title"]')

    primary_image_url = ""
    photo_block = soup.find("div", {"data-test": "photo-block"})
    if photo_block:
        img_tag = photo_block.find("img")
        if img_tag and img_tag.get("src"):
            primary_image_url = img_tag["src"]

    sales_method = soup.select_one('h3[data-test="pricing-method__price"]')
    features = await scrape_features(soup)
    listed_date = soup.select_one('span[data-test="description__listed-date"]')
    capital_value = soup.select_one('div[data-test="capital-valuation"] h4')

    return {
        "extractDate": extract_date,
        "listingUrl": url,
        "agentNames": merged_names,
        "agencyName": agency_name.get_text(strip=True) if agency_name else "",
        "primaryImageUrl": primary_image_url if primary_image_url else "",
        "propertyAddress": property_address.get_text(strip=True) if property_address else "",
        "salesMethod": sales_method.get_text(strip=True) if sales_method else "",
        "propertyType": features.get("property_type", ""),
        "bedrooms": features.get("bedroom", ""),
        "bathrooms": features.get("bathroom", ""),
        "parkingSpace": features.get("garage", ""),
        "floorArea": features.get("floor_area", ""),
        "landArea": features.get("land_area", ""),
        "listingDate": listed_date.get_text(strip=True) if listed_date else "",
        "capitalValue": capital_value.get_text(strip=True) if capital_value else "",
    }

async def get_total_pages_from_soup(soup):
    page_links = soup.select('div[data-test="paginated-items"] > div > a.paginated-items__page-number')
    page_numbers = [int(a.text.strip()) for a in page_links if a.text.strip().isdigit()]
    return max(page_numbers) if page_numbers else 1

async def main():
    async with Actor:
        # Get input configuration
        actor_input = await Actor.get_input() or {}
        max_pages = actor_input.get('maxPages', 3)
        location = actor_input.get('location', 'queenstown')
        min_delay = actor_input.get('minDelay', 1.5)
        max_delay = actor_input.get('maxDelay', 4.0)

        Actor.log.info(f'Starting scraper for {location} with max {max_pages} pages')

        # Construct URLs based on location
        if location.lower() == 'queenstown':
            start_url_base = "https://www.realestate.co.nz/residential/sale/central-otago-lakes-district/queenstown"
        else:
            # For other locations, you might need to modify this
            start_url_base = f"https://www.realestate.co.nz/residential/sale/{location}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Set user agent to avoid detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            current_page = 1
            total_listings_scraped = 0

            while True:
                current_url = start_url_base if current_page == 1 else f"{start_url_base}?page={current_page}"
                Actor.log.info(f"Visiting page {current_page}: {current_url}")

                try:
                    await page.goto(current_url, wait_until='networkidle')
                    soup = await auto_scroll(page)

                    if current_page == 1:
                        total_pages = await get_total_pages_from_soup(soup)
                        total_pages = min(total_pages, max_pages)
                        Actor.log.info(f"Scraping up to {total_pages} page(s).")

                    urls = extract_listing_urls(soup)
                    Actor.log.info(f"Found {len(urls)} listing URLs on page {current_page}")

                    for i, url in enumerate(urls, 1):
                        Actor.log.info(f"[Page {current_page} - {i}/{len(urls)}] Scraping: {url}")
                        try:
                            data = await scrape_details(page, url)

                            # Push data to Apify dataset
                            await Actor.push_data(data)
                            total_listings_scraped += 1

                            # Random delay between requests
                            delay = random.uniform(min_delay, max_delay)
                            Actor.log.info(f"Sleeping for {delay:.2f} seconds...")
                            await asyncio.sleep(delay)

                        except Exception as e:
                            Actor.log.error(f"Error scraping {url}: {e}")
                            continue

                    if current_page >= total_pages:
                        break

                    current_page += 1

                except Exception as e:
                    Actor.log.error(f"Error processing page {current_page}: {e}")
                    break

            await browser.close()

            Actor.log.info(f"Scraping completed! Total listings scraped: {total_listings_scraped}")

if __name__ == "__main__":
    asyncio.run(main())