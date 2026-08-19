import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    is_prod = os.getenv("APP_ENV") == "production"

    print("\n" + "=" * 60)
    print("🚀 60-Day CSE Job Prep Automation Platform is starting...")
    print(f"🔗 Server listening on: http://{host}:{port}")
    print("=" * 60 + "\n")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=not is_prod,
    )