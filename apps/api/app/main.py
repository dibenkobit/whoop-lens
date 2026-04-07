from fastapi import FastAPI

app = FastAPI(title="Whoop Lens API", version="0.1.0")


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "whoop-lens-api", "version": "0.1.0"}
