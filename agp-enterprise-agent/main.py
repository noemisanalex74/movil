# main.py
import uvicorn

if __name__ == "__main__":
    print("Starting AGP Enterprise Agent API server...")
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True, # Use reload for development
        log_level="info"
    )
