from bs4 import BeautifulSoup
import logging
import scraperwiki
import sqlite3
import time
import urllib2

logging.basicConfig(level=logging.DEBUG)

scrape_url = 'https://eservices.holroyd.nsw.gov.au/eservice/daEnquiry/currentlyAdvertised.do?nodeNum=54422'
comment_url = 'mailto:hcc@holroyd.nsw.gov.au?subject='
date_scraped = time.strftime('%Y-%m-%d')

html = urllib2.urlopen(scrape_url)
soup = BeautifulSoup(html.read())

# Structure of the html for one DA:
# <h4 class='non_table_headers'>
#   <a>Address for DA1</a>
# </h4>
# <div>
#   <p class='rowDataOnly'>
#     <span class='key'>Key1</span>
#     <span class='inputField'>Value1</span>
#   </p>
#   <p class='rowDataOnly'>
#     <span class='key'>Key2</span>
#     <span class='inputField'>Value2</span>
#   </p>
#   ...
# </div>
for listing in soup.find_all('h4', 'non_table_headers'):
  record = {
    'address': str(listing.a.string),
    'date_scraped': date_scraped,
    'info_url': scrape_url,
  }

  for row in listing.next_sibling.find_all('p', 'rowDataOnly'):
    key = row.find_all('span', 'key')[0].string
    value = str(row.find_all('span', 'inputField')[0].string)

    if key == 'Application No.':
      record['council_reference'] = value
      record['comment_url'] = comment_url + urllib2.quote('Development Application Enquiry: ' + value, '')
    elif key == 'Type of Work':
      record['description'] = value
    elif key == 'Date Lodged':
      record['date_received'] = time.strftime('%Y-%m-%d', time.strptime(value, '%d/%m/%Y'))

  # Skip if there is no valid council reference number found.
  if ('council_reference' not in record or
      not record['council_reference']):
    continue

  logging.info('Writing record to sqlite: ' + record['council_reference'])
  scraperwiki.sqlite.save(unique_keys=['council_reference'], data=record)
