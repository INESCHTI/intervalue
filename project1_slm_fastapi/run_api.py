from src.slm_api.main import app


def main() -> None:
    import uvicorn

    print("Starting Project 1 API on http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
