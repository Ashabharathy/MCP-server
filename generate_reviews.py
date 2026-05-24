"""
Generate additional synthetic reviews to reach 500 total reviews.
"""
import random
from datetime import datetime, timedelta

# Existing review themes and patterns
positive_themes = [
    ("Easy SIP setup", "Setting up my SIP on GROWW was incredibly smooth. The interface is intuitive and the process took less than 5 minutes."),
    ("Great returns", "My portfolio has grown significantly over the past year. The XIRR tracking is accurate and transparent."),
    ("Fast execution", "Orders are executed quickly and NAV allotment happens the same day. Very efficient platform."),
    ("Good customer support", "Had an issue with my SIP and support resolved it within an hour via chat. Professional service."),
    ("Clean interface", "The app design is clean and easy to navigate. Finding funds and managing investments is straightforward."),
    ("Low minimum investment", "Started with just 100 rupees. The low minimum makes investing accessible to everyone."),
    ("Tax reports helpful", "The auto-generated tax reports saved me hours of manual work for filing returns."),
    ("Watchlist alerts work", "NAV alerts for my watchlist funds arrive promptly. Great for tracking entry points."),
    ("KYC was smooth", "Completed video KYC in under 20 minutes. No paperwork needed, very convenient."),
    ("Portfolio tracking", "Real-time portfolio updates and XIRR calculations are accurate. I trust the numbers completely."),
]

negative_themes = [
    ("App crashes frequently", "The app crashes randomly when switching between tabs. Happens multiple times per day."),
    ("Payment failures", "UPI payments fail consistently during peak hours. Have to retry multiple times to complete transactions."),
    ("Withdrawal delays", "My withdrawal request has been pending for over two weeks. Support tickets go unanswered."),
    ("KYC rejection", "My KYC was rejected multiple times despite submitting clear documents. No explanation provided."),
    ("Statement download broken", "Cannot download tax statements. The PDF is blank or shows error 500 every time."),
    ("Account locked", "Account locked after wrong MPIN attempts. Support queue wait time is over 45 minutes."),
    ("Duplicate charges", "Was charged twice for a single transaction. Refund process is slow and frustrating."),
    ("Portfolio value wrong", "Portfolio shows incorrect value that doesn't match actual holdings. Discrepancy persists."),
    ("OTP issues", "OTP never arrives on my registered number. Login is impossible without email reset."),
    ("App performance slow", "After recent updates, the app is noticeably slower. Pages take 5+ seconds to load."),
]

neutral_themes = [
    ("Need web version", "Prefer managing investments on laptop. A web portal would make this a complete product."),
    ("More fund options", "Wish there were more international fund options for global exposure."),
    ("Dark mode request", "Bright interface strains eyes at night. Dark mode would be very helpful."),
    ("Budget integration", "Would like to see how SIP commitments relate to overall budget planning."),
    ("Partial withdrawals", "Cannot withdraw partial amounts from lumpsum investments. Need full redemption."),
    ("Custom benchmarks", "Want to compare portfolio against custom benchmarks like Nifty 50."),
    ("Multi-account support", "Managing multiple family accounts requires full logout each time. Inconvenient."),
    ("Export watchlist", "No option to export or share watchlist data. Have to maintain separate spreadsheet."),
    ("Fund manager info", "Cannot find detailed fund manager track records. Important for evaluating funds."),
    ("NAV history length", "NAV history only shows 3 months. Need longer history for proper analysis."),
]

def generate_review(review_id, date):
    """Generate a single review with random rating and theme."""
    # Weighted distribution: more positive (4-5), some neutral (3), fewer negative (1-2)
    rating_weights = [5, 10, 25, 35, 25]  # 1-star: 5%, 2-star: 10%, 3-star: 25%, 4-star: 35%, 5-star: 25%
    rating = random.choices([1, 2, 3, 4, 5], weights=rating_weights)[0]
    
    if rating >= 4:
        title, text = random.choice(positive_themes)
    elif rating == 3:
        title, text = random.choice(neutral_themes)
    else:
        title, text = random.choice(negative_themes)
    
    # Vary the text slightly to avoid duplicates
    variations = [
        text,
        text + " This has been my experience with the app.",
        text + " Hope this gets addressed in future updates.",
        text + " Overall, still using the app but this needs work.",
    ]
    text = random.choice(variations)
    
    # App version code (620-652 range)
    version = random.randint(620, 652)
    
    # Random time
    hour = random.randint(8, 18)
    minute = random.choice([0, 15, 30, 45])
    time_str = f"{hour:02d}:{minute:02d}:00"
    
    date_str = f"{date.strftime('%Y-%m-%d')} {time_str} UTC"
    
    return f"{rating},{title},{text},{date_str},{version},"

# Generate 500 reviews
# Start from 2026-02-27 and go to 2026-05-24 (12 weeks)
start_date = datetime(2026, 2, 27)
end_date = datetime(2026, 5, 24)
total_days = (end_date - start_date).days

reviews = []
header = "Star Rating,Review Title,Review Text,Review Submit Date and Time,App Version Code,Developer Reply Text\n"
reviews.append(header)

# Generate reviews distributed across the date range
for i in range(500):
    days_offset = random.randint(0, total_days)
    review_date = start_date + timedelta(days=days_offset)
    review = generate_review(i + 1, review_date)
    reviews.append(review + "\n")

# Write to file
with open("ingestion/sample_data/playstore_sample.csv", "w", encoding="utf-8") as f:
    f.writelines(reviews)

print(f"Generated 500 reviews and saved to ingestion/sample_data/playstore_sample.csv")
