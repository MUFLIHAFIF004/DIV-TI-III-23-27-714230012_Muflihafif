from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Mount folder public untuk file statis jika diakses langsung
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")

if os.path.exists(public_dir):
    app.mount("/static", StaticFiles(directory=public_dir), name="static")

@app.get("/")
def read_root():
    index_file = os.path.join(public_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Agentic Testing API is running"}