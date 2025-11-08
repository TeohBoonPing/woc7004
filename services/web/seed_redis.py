import os
import redis
from project import app, db
from project.models import ShortLink

redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

NUM_FIXED_URLS = int(os.environ.get('NUM_FIXED_URLS', 10000))

def seed_redis_shortlinks():
    print(f"Seeding {NUM_FIXED_URLS} shortlinks into Redis...")

    for i in range(NUM_FIXED_URLS):
        original_url = f"https://example.com/{i}"
        short_url = f"t{i}"
        redis_client.set(f"longurl:{original_url}", short_url)

    print("✅ Redis seeding complete!")

if __name__ == "__main__":
    seed_redis_shortlinks()
