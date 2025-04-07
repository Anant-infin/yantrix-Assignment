import re
import json
import csv
import requests
import spacy
from bs4 import BeautifulSoup

# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

# Sending request with headers
headers = {
    "User -Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) "
                   "Chrome/91.0.4472.124 Safari/537.36"
}

# Correctly formatted URL
base_url = "https://www.finsmes.com/category/uk/page/"
start_page = 1
end_page = 5

# To access Articles pages in url
def generate_urls(start, end):
    return [f"{base_url}{page_num}" for page_num in range(start, end + 1)]

# Url page Error handeling
def fetch_page(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching webpage {url}: {e}")
        return None

# For Extracting Article data
def extract_article_data(soup):
    articles = soup.find_all('h3', class_= 'entry-title td-module-title')
    data = []

    for article in articles:
        title = article.get_text()
        link = article.find('a')['href'] if article.find('a') else ''
        excerpt_div = article.find_next_sibling('div', class_='td-excerpt')
        excerpt = excerpt_div.get_text() if excerpt_div else ''

        location_parts = [part.strip() for part in excerpt.split(',')] if excerpt else []
        city = location_parts[0] if len(location_parts) > 0 else ''
        country = location_parts[1] if len(location_parts) > 1 else ''

        funding_amounts = extract_funding_amounts(link)
        CEO_CTO_CFO_name = extract_CEO_CTO_CFO(link)
        article_date = extract_article_date(link)

        data.append({
            'title': title,
            'link': link,
            'country_address': {
                'city': city,
                'state': 'None',  # Assuming state is not given
                'country': country
            },
            'funding_amount': funding_amounts,
            'ceo_cto_cfo_name': CEO_CTO_CFO_name,  # Placeholder for CEO/CTO/CFO name
            'Article_date': article_date,
            'entity_name': extract_entities(title)
        })

    return data

# Extracting Entity names
def extract_entities(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == 'ORG']

# Rxtracting raised fund Amount
def extract_funding_amounts(link):
    response_text = fetch_page(link)
    if response_text is None:
        return []

    soup = BeautifulSoup(response_text, 'html.parser')
    paragraphs = soup.find_all('p')
    text_content = ' '.join([para.get_text() for para in paragraphs])

    doc = nlp(text_content)
    return [ent.text for ent in doc.ents if ent.label_ == 'MONEY']

# extracting article date
def extract_article_date(url):
    response_text = fetch_page(url)
    if response_text is None:
        return None

    soup = BeautifulSoup(response_text, 'html.parser')
    time_element = soup.find('time', class_='entry-date updated td-module-date')
    if time_element:
        date_text = time_element.get_text(strip=True)
        doc = nlp(date_text)
        for ent in doc.ents:
            if ent.label_ == "DATE":
                return ent.text
    return None

# Extracting CEO/CTO/CFO names from article link
def extract_CEO_CTO_CFO(link):
    """Extract paragraphs from the given link and return CEO, CTO, and CFO names."""
    response_text = fetch_page(link)
    if response_text is None:
        return []

    soup = BeautifulSoup(response_text, 'html.parser')
    paragraphs = soup.find_all('p')
    paragraph_texts = ' '.join([para.get_text(strip=True) for para in paragraphs])

    # Extract names of CEO, CTO, and CFO
    names = CEO_CTO_CFO(paragraph_texts)

    return names


def CEO_CTO_CFO(paragraphs):
    """Extract CEO, CTO, and CFO names from the given text."""
    # Define a regex pattern to match CEO, CTO, and CFO names
    pattern = r'\b(?:CEO|CTO|CFO)\s*[:\-]?\s*([A-Z][a-zA-Z\s-]*)'

    # Find all matches in the text
    matches = re.findall(pattern, paragraphs)

    # Extract names from matches
    names = [name.strip() for name in matches if name]

    return names
def main():
    urls = generate_urls(start_page, end_page)
    all_data = []

    for url in urls:
        page_content = fetch_page(url)
        if page_content:
            soup = BeautifulSoup(page_content, 'html.parser')
            article_data = extract_article_data(soup)
            all_data.extend(article_data)

    # Save the extracted data to a JSON file
    with open('extracted_data.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(all_data, jsonfile, ensure_ascii=False, indent=4)
    with open('extracted_data.csv', 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_data[0].keys())
        writer.writeheader()
        writer.writerows(all_data)

    print("Data has been extracted and saved to 'extracted_data.json' and 'extracted_data.csv' .")


if __name__ == "__main__":
    main()