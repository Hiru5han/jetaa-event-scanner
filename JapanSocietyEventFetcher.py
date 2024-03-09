import requests
from bs4 import BeautifulSoup

class JapanSocietyEventFetcher:
    def __init__(self):
        self.base_url = 'https://www.japansociety.org.uk/events'
        self.session = requests.Session()  # Use session for persistent connection
        # self.events = existing_events

    def scrape_events_from_url(self, url, existing_events):
        response = self.session.get(url)
        response.raise_for_status()  # Make sure the request was successful

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all event card bodies
        event_cards = soup.find_all('div', class_='card')  # Find all event card divs

        for card in event_cards:
            # Extract event details
            event_details = self.extract_event_details(card)
            if event_details:
                existing_events.append(event_details)

    def extract_event_details(self, card):
        # Extracts event details from a card and returns a tuple
        event_source = "japan_society"
        event_location = "Not Available"
        event_time = "Not Available"
        event_price = "Not Available"

        url_container = card.find('div', class_='border-top')
        event_link = url_container.find('a', href=True) if url_container else None
        event_url = event_link['href'] if event_link else 'URL not found'

        event_date_span = card.find('span', class_='js-event-date')
        event_date = event_date_span.text.strip() if event_date_span else 'Date not found'

        event_name_span = card.find('span', class_='card-text')
        event_name = event_name_span.text.strip() if event_name_span else 'Title not found'

        if event_name == 'Title not found' and event_date == 'Date not found' and event_url == 'URL not found':
            return None
        else:
            return (event_source, event_name, event_location, event_date, event_time, event_price, event_url)


    def get_pagination_urls(self, soup):
        # Extracts and returns pagination URLs
        pagination_links = soup.find_all('a', class_='page-link')
        page_urls = [link.get('href') for link in pagination_links if link.get('href') and link.get('href') != '#']
        return page_urls

    def combine_and_return_events(self, existing_events):
        # Handle the initial page
        self.scrape_events_from_url(self.base_url, existing_events)
        
        # Get pagination URLs
        initial_response = self.session.get(self.base_url)
        initial_response.raise_for_status()
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        page_urls = self.get_pagination_urls(initial_soup)
        
        # Deduplicate and ensure we only proceed if there are additional pages
        unique_page_urls = sorted(set(page_urls), key=page_urls.index)
        for page_url in unique_page_urls:
            # Ensure full URL (if necessary, adjust based on actual href values)
            if not page_url.startswith('http'):
                page_url = self.base_url + page_url
            self.scrape_events_from_url(page_url, existing_events)

        return existing_events
