import json

with open('ingestion/output/reviews.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total refined reviews: {data['summary']['total']}")
print(f"Play Store reviews: {data['summary']['playstore']}")
print(f"Date range: {data['summary']['date_min']} to {data['summary']['date_max']}")
print(f"Rating distribution: {data['summary']['ratings_distribution']}")
