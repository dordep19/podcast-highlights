"""
This file implements the REST API that serves podcast transcript uploads and
requests for suggested podcast highlights. 
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from starlette.responses import RedirectResponse

from highlighter import Highlighter


app = FastAPI()
highlighter = Highlighter()


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.post("/analyze")
def analyze_file(time: int, file: UploadFile = File(...)):
    id = highlighter.analyze(time, file)

    return {
        "file_id": id
    }


@app.get("/highlights")
def get_highlights(id: int):
    try:
        return {
            "file_id": id,
            "highlights": highlighter.highlights(id)
        }
    except:
        raise HTTPException(status_code=400, 
            detail="Failed to retrieve highlights for file {}".format(id))
