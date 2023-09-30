import csv
import requests

# Spreadsheet ID from the sheet URL
spreadsheet_id = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms' 

# API URL to download sheet data
url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv'

# Make API request
response = requests.get(url)

# Parse CSV content
data = response.content.decode('utf-8')
reader = csv.reader(data.splitlines())

# Convert to list of lists
table = list(reader)
