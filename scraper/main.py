import logging

# Configure global logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Import pipeline steps
from scraper import (
    discover_navigation,
    extract_product_links,
    scrape_product_pages,
    parse_flat_product_data,
    recipe_scraper,
    recipe_full_details,
    get_about_page_links,
    scrape_full_about
)

def main():
    logger.info("🚀 Starting full scraping pipeline...\n")

    # Product scraping
    discover_navigation.run()
    extract_product_links.run()
    scrape_product_pages.run()
    parse_flat_product_data.run()

    # Recipe scraping
    recipe_scraper.run()
    recipe_full_details.run()

    # Article scraping
    get_about_page_links.run()
    scrape_full_about.run()

    logger.info("\n✅ Scraping pipeline completed successfully.")

if __name__ == "__main__":
    main()
