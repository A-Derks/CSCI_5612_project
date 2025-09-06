from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI(title="CSCI 5612 Class Project")

# Static & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---------- Pages ----------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    me = {"name": "The Wait Time Problem", "tagline": "Predicting Disney's Ride Wait Times"}
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home", "me": me})

@app.get("/introduction", response_class=HTMLResponse)
async def introduction(request: Request):
    return templates.TemplateResponse("introduction.html", {"request": request, "title": "Introduction"})

@app.get("/tab1", response_class=HTMLResponse)
async def data_prep(request: Request):
    return templates.TemplateResponse("data_prep.html", {"request": request, "title": "Data Prep"})

@app.get("/tab2", response_class=HTMLResponse)
async def clustering(request: Request):
    return templates.TemplateResponse("clustering.html", {"request": request, "title": "Clustering"})

@app.get("/tab3", response_class=HTMLResponse)
async def pca(request: Request):
    return templates.TemplateResponse("pca.html", {"request": request, "title": "PCA"})

@app.get("/tab4", response_class=HTMLResponse)
async def dt(request: Request):
    return templates.TemplateResponse("dt.html", {"request": request, "title": "DT"})

@app.get("/tab5", response_class=HTMLResponse)
async def nb(request: Request):
    return templates.TemplateResponse("nb.html", {"request": request, "title": "NB"})

@app.get("/tab6", response_class=HTMLResponse)
async def svm(request: Request):
    return templates.TemplateResponse("svm.html", {"request": request, "title": "SVM"})

@app.get("/tab7", response_class=HTMLResponse)
async def regression(request: Request):
    return templates.TemplateResponse("regression.html", {"request": request, "title": "Regression"})

@app.get("/tab8", response_class=HTMLResponse)
async def nn(request: Request):
    return templates.TemplateResponse("nn.html", {"request": request, "title": "NN"})
