import uvicorn


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 60-Day CSE Job Prep Automation Platform is starting...")
    print("🔗 Open in your browser: http://127.0.0.1:8000")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )