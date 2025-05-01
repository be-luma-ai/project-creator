# scripts/main.py

from fastapi import FastAPI
import os
import uvicorn
import sys
import pathlib

# Agrega el root del proyecto al sys.path para que funcionen los imports
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

# Importa la función main desde run_pipeline.py
from scripts.run_pipeline import run_pipeline as pipeline_main 


app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/run-pipeline")
def run_pipeline():
    print("🔥 [run_pipeline] started")
    try:
        pipeline_main()
        return {"status": "✅ Pipeline executed successfully"}
    except Exception as e:
        print("❌ Error in run_pipeline:", e)
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("scripts.main:app", host="0.0.0.0", port=port)