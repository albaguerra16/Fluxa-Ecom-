from decouple import config

MELI_ACCESS_TOKEN: str = config("MELI_ACCESS_TOKEN", default="")
ML_APP_ID: str = config("ML_APP_ID", default="")
ML_APP_SECRET: str = config("ML_APP_SECRET", default="")
TRENDS_GEO: str = config("TRENDS_GEO", default="CO")
SCORE_THRESHOLD: int = config("SCORE_THRESHOLD", default=60, cast=int)
VIDEO_VARIATIONS: int = config("VIDEO_VARIATIONS", default=3, cast=int)

ANTHROPIC_API_KEY: str = config("ANTHROPIC_API_KEY", default="")
SHOPIFY_STORE_URL: str = config("SHOPIFY_STORE_URL", default="")
SHOPIFY_ACCESS_TOKEN: str = config("SHOPIFY_ACCESS_TOKEN", default="")
FAL_KEY: str = config("FAL_KEY", default="")
