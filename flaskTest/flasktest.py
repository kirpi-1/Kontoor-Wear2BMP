import os, stat
from flask import Flask, flash, request, redirect, url_for, send_file, Response
from werkzeug.utils import secure_filename
import shutil


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER