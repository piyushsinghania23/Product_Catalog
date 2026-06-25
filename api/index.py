from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
import os
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app as fastapi_app

app = fastapi_app
