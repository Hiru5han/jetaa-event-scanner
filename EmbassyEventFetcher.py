import requests
from bs4 import BeautifulSoup

class EmbassyEventFetcher:
    def __init__(self, year):
        self.base_url = 'https://www.uk.emb-japan.go.jp/JAPANUKEvent/event/'
        self.year = year
        self.short_year = str(year)[2:]

    def combine_and_return_events(self, events):
        for month in range(1, 13):
            month_str = str(month).zfill(2)
            url = self.base_url + f'eve-list{self.short_year}-{month_str}.html'
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            # Ensure the correct handling of encoding
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                event_blocks = soup.findAll('div', class_='card-wrapper')
                
                for block in event_blocks:
                    event_url_suffix = block.find('a')['href']
                    event_url = self.base_url + event_url_suffix
                    event_name = block.find('h4', class_='card-title').text.strip()
                    date_location_str = block.find('p', class_='mbr-text').text.strip().split('\r\n')
                    event_date = date_location_str[0].strip()
                    event_location = date_location_str[1].strip() if len(date_location_str) > 1 else "Not Available"
                    
                    events.append(("embassy", event_name, event_location, event_date, "Not Available", "Not Available", event_url))
            else:
                print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return events
