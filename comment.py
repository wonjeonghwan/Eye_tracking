import requests
import pandas as pd

def get_steam_reviews(app_id, num_pages=50):
    reviews = []
    cursor = "*"
    
    for page in range(num_pages):
        url = (
            f"https://store.steampowered.com/appreviews/{app_id}"
            f"?json=1&num_per_page=100&language=all&purchase_type=all"
            f"&cursor={cursor}&filter=all"
        )
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Debug: check the response structure.
            if "reviews" not in data:
                print(f"응답에 'reviews' 키가 없습니다. page {page}의 데이터 키:", list(data.keys()))
                break
            
            for review in data['reviews']:
                reviews.append({
                    "review": review.get("review", ""),
                    "voted_up": review.get("voted_up", False),
                    "votes_up": review.get("votes_up", 0),
                    "timestamp_created": review.get("timestamp_created", 0)
                })
            
            # Update cursor
            cursor = data.get('cursor', "")
            if not cursor:
                print("더 이상 가져올 리뷰가 없습니다. (cursor 없음)")
                break
        else:
            print(f"page {page} 에러, 상태 코드: {response.status_code}")
            break

    return pd.DataFrame(reviews)

# appID: Getting Over It with Bennett Foddy (가정: 240720)
app_id = 240720

# Fetch the reviews with a higher page count to cover the whole period
reviews_df = get_steam_reviews(app_id, num_pages=10)

if reviews_df.empty:
    print("리뷰 데이터가 없습니다.")
else:
    reviews_df['datetime'] = pd.to_datetime(reviews_df['timestamp_created'], unit='s')
    reviews_df.set_index('datetime', inplace=True)
    
    # Monthly and weekly review counts over the entire period
    monthly_review_counts = reviews_df.resample('M').size()
    weekly_review_counts = reviews_df.resample('W').size()

    print("=== 월별 리뷰 수 ===")
    print(monthly_review_counts)

    print("\n=== 주별 리뷰 수 ===")
    print(weekly_review_counts)
