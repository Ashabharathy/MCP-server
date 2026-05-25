"""
review_generator.py — Generate high-volume, realistic, synthetic review data.

This utility helps test the ingestion, scaling, and processing pipelines of the
GROWW Mutual Fund FAQ Assistant by generating up to 10,000+ reviews with realistic
distributions, themes, dates, and ratings.
"""

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Themes & Content Templates ───────────────────────────────────────────────

THEMES = {
    "KYC": {
        "ratings": [1, 2, 3],
        "starters": [
            "KYC is extremely frustrating.",
            "My Aadhaar verification has been pending for days.",
            "Video KYC is a nightmare.",
            "Document upload keeps failing.",
            "Unable to complete my onboarding profile.",
        ],
        "middles": [
            "I uploaded clear, high-resolution photos of my PAN and Aadhaar but the system keeps saying documents are illegible.",
            "The live video verification call drops consistently after waiting in the queue for 15 minutes.",
            "No human customer support agent is available to verify my uploaded documents.",
            "It gives a random error code during the signature upload step and resets the whole process.",
            "My application was rejected four times without any specific reason or feedback.",
        ],
        "endings": [
            "Please fix this onboarding bug immediately.",
            "Extremely disappointed with the onboarding flow.",
            "If this isn't resolved soon, I will switch to another investment app.",
            "Support is totally unresponsive to my tickets.",
            "Not a good start for a new investor.",
        ],
    },
    "Payments": {
        "ratings": [1, 2, 3],
        "starters": [
            "Money was debited from my bank account but my portfolio is not updated.",
            "UPI transaction failed at the last confirmation step.",
            "Net banking payment is completely broken on this app.",
            "Double deduction occurred during lumpsum investment.",
            "Autopay setup failed but bank still got linked.",
        ],
        "middles": [
            "I invested 10,000 rupees via UPI, the bank sent a success SMS, but the app displays a payment failed screen.",
            "The payment screen times out and crashes back to the dashboard during peak market hours.",
            "I tried paying via HDFC net banking but it stuck at the gateway redirection page indefinitely.",
            "My bank statement confirms the debit, yet the app shows zero transaction history for this payment.",
            "The payment was deducted twice for a single SIP installment and no refund has been initiated.",
        ],
        "endings": [
            "Very worried about where my hard-earned money went.",
            "Please process my allotment or refund my money immediately.",
            "Customer support only sends automated template replies about this.",
            "This payment gateway issue makes the app unreliable.",
            "Hoping my money is safe with this platform.",
        ],
    },
    "Onboarding": {
        "ratings": [1, 2, 3, 4],
        "starters": [
            "The onboarding UI is a bit confusing.",
            "Too many steps required just to get started.",
            "App lock and biometric setup is buggy.",
            "Onboarding took much longer than advertised.",
            "The interface is clean but the sign-up process is tedious.",
        ],
        "middles": [
            "Setting up fingerprint login resets my MPIN every single time I restart the phone.",
            "The app freezes for 10 seconds right after entering the welcome screen OTP.",
            "There are too many document requirements and no clear instructions on what size PDF to upload.",
            "I had to re-enter my personal details three times because the app crashed mid-way.",
            "The tutorial screens cannot be skipped, which is annoying for experienced investors.",
        ],
        "endings": [
            "Please simplify the verification screens.",
            "Needs a smoother registration flow for non-tech-savvy users.",
            "Otherwise, the rest of the application seems well-designed.",
            "Hoping the actual investing experience is better than the sign-up.",
            "Decent app but onboarding friction is high.",
        ],
    },
    "Statements": {
        "ratings": [1, 2, 3, 4],
        "starters": [
            "Downloading tax statements is broken.",
            "The annual portfolio report contains blank pages.",
            "Exporting my mutual fund statement gives a server error.",
            "Capital gains calculations are incorrect.",
            "Wish there was a better way to export watchlist data.",
        ],
        "middles": [
            "The download button in the tax section opens a 0 KB corrupt PDF that won't open in Acrobat.",
            "XIRR calculations in the exported Excel spreadsheet do not match the values shown in the mobile UI.",
            "The system keeps throwing a 500 internal server error when I request my FY25 capital gains report.",
            "It lacks detail on short-term vs long-term capital gains, making tax filing very complicated.",
            "My mutual fund transactions are listed correctly, but the overall summary values are blank.",
        ],
        "endings": [
            "This is a critical bug during tax filing season.",
            "Please fix the PDF export tool as soon as possible.",
            "I need this statement urgently for my CA.",
            "Excel sheet format should be cleaned up.",
            "A simple share button is needed.",
        ],
    },
    "Withdrawals": {
        "ratings": [1, 2, 3],
        "starters": [
            "Redemption request is stuck in pending state for a week.",
            "Unable to withdraw my money from liquid funds.",
            "Withdrawal was rejected with no explanation given.",
            "Payout is delayed beyond the promised T+2 days.",
            "Stuck in verification when trying to redeem mutual funds.",
        ],
        "middles": [
            "I submitted a withdrawal request 10 days ago, the units were debited from my portfolio, but no money has reached my bank.",
            "The instant redemption feature says it transfers money in 30 minutes, but it has been 4 hours and nothing happened.",
            "Support claims the payout was successful, but my bank statement shows absolutely no deposit from their side.",
            "The cancel button for pending withdrawals does not work, it just shows a loading spinner forever.",
            "Trying to update my primary bank account for withdrawal is locked and support ticket is ignored.",
        ],
        "endings": [
            "This delay is completely unacceptable for a financial app.",
            "Where is my money? Urgent response required.",
            "Very disappointed with this lack of liquidity control.",
            "I will file a complaint if my payout isn't processed today.",
            "Zero transparency on withdrawal status.",
        ],
    },
    "Praise": {
        "ratings": [4, 5],
        "starters": [
            "Best investment app in India!",
            "Super smooth and intuitive mutual fund interface.",
            "Highly recommended for beginners and pro investors alike.",
            "I have been using this app for 2 years without a single issue.",
            "The design is incredibly beautiful and fast.",
        ],
        "middles": [
            "Setting up monthly SIPs is absolutely seamless and the auto-pay works flawlessly every single time.",
            "I love the side-by-side fund comparison tool and the portfolio overlap analysis which helped me rebalance.",
            "Instant KYC was completed in under 15 minutes on a Sunday and I started my first investment immediately.",
            "The app performance is extremely fast, charts load instantly, and the XIRR tracking is very transparent.",
            "Low minimum investment limits of just 100 rupees make mutual funds highly accessible to everyone.",
        ],
        "endings": [
            "Kudos to the development team for such a brilliant product!",
            "Will definitely continue using this for all my wealth building.",
            "Keep up the great work and thank you for making investing simple.",
            "Five stars all the way!",
            "The dark mode is also beautifully implemented and comfortable.",
        ],
    },
}

# ── Generation Core ──────────────────────────────────────────────────────────

def generate_review_text(theme_key: str, rating: int) -> tuple[str, str]:
    """Assemble a realistic review title and body text based on theme and rating."""
    theme_data = THEMES[theme_key]
    
    starter = random.choice(theme_data["starters"])
    middle = random.choice(theme_data["middles"])
    ending = random.choice(theme_data["endings"])
    
    # Title is usually a shortened or paraphrased starter
    title_words = starter.rstrip("!.").split()
    title = " ".join(title_words[:random.randint(3, 6)])
    
    # Text combines them
    text = f"{starter} {middle} {ending}"
    
    return title, text


def generate_dataset(
    count: int = 10000,
    weeks: int = 12,
    reference_date: datetime = None
) -> list[dict]:
    """
    Generate a list of synthetic reviews matching the Google Play Store schema.
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc).replace(tzinfo=None)
        
    start_date = reference_date - timedelta(weeks=weeks)
    total_seconds = int((reference_date - start_date).total_seconds())
    
    reviews = []
    
    # Target distribution of ratings:
    # 5-Star: 30%, 4-Star: 20%, 3-Star: 15%, 2-Star: 15%, 1-Star: 20%
    rating_choices = [5] * 30 + [4] * 20 + [3] * 15 + [2] * 15 + [1] * 20
    
    for i in range(count):
        rating = random.choice(rating_choices)
        
        # Select theme compatible with the rating
        eligible_themes = []
        for theme_key, theme_data in THEMES.items():
            if rating in theme_data["ratings"]:
                eligible_themes.append(theme_key)
                
        theme = random.choice(eligible_themes)
        title, text = generate_review_text(theme, rating)
        
        # Random timestamp in the window
        random_seconds = random.randint(0, total_seconds)
        review_date = start_date + timedelta(seconds=random_seconds)
        date_str = review_date.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        app_version = random.randint(610, 655)
        
        reviews.append({
            "Star Rating": rating,
            "Review Title": title,
            "Review Text": text,
            "Review Submit Date and Time": date_str,
            "App Version Code": app_version,
            "Developer Reply Text": ""
        })
        
    # Sort by date descending
    reviews.sort(key=lambda r: r["Review Submit Date and Time"], reverse=True)
    return reviews


def write_to_csv(reviews: list[dict], output_path: Path) -> None:
    """Write generated reviews to a Google Play Console formatted CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    headers = [
        "Star Rating",
        "Review Title",
        "Review Text",
        "Review Submit Date and Time",
        "App Version Code",
        "Developer Reply Text"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(reviews)


# ── Executable Entrypoint ────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic high-volume reviews CSV.")
    parser.add_argument("--count", type=int, default=10000, help="Number of reviews to generate (default: 10000)")
    parser.add_argument("--weeks", type=int, default=12, help="Look-back window in weeks (default: 12)")
    parser.add_argument("--out", type=str, default=None, help="Output path (default: ingestion/sample_data/playstore_10k_sample.csv)")
    
    args = parser.parse_args()
    
    root_dir = Path(__file__).parent.parent
    output_file = Path(args.out) if args.out else root_dir / "ingestion" / "sample_data" / "playstore_10k_sample.csv"
    
    print(f"Generating {args.count} synthetic GROWW reviews over a {args.weeks}-week window...")
    records = generate_dataset(count=args.count, weeks=args.weeks)
    
    print(f"Saving to {output_file}...")
    write_to_csv(records, output_file)
    
    print("Success! File generated successfully.")
