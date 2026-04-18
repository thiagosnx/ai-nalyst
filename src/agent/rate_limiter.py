from langchain_core.rate_limiters import InMemoryRateLimiter

# ~9 requisições por minuto para não estourar o GitHub Models free tier
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.15,
    check_every_n_seconds=0.1,
    max_bucket_size=10,
)
