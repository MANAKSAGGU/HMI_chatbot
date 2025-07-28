from fastapi import FastAPI, Form, File, UploadFile, Request, Response, Depends, Cookie, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, shutil, uuid, subprocess, sqlite3, hashlib
from typing import Optional

app = FastAPI()

# --------- Setup Paths ---------
UPLOAD_FOLDER = "uploads"
TEMPLATE_DIR = "templates"
DB_PATH = "users.db"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# --------- DB Setup ---------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                query TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
init_db()

video_status = {}  # job_id -> {"status": "pending"|"completed"|"error", "url": str}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --------- Helper ---------
def get_user_by_username(username: str):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

def save_video_for_user(user_id: int, filename: str, query: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO videos (user_id, filename, query) VALUES (?, ?, ?)", (user_id, filename, query))

def get_videos_by_user(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT id, filename, query FROM videos WHERE user_id = ?", (user_id,)).fetchall()

def delete_video_for_user(user_id: int, video_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        video = conn.execute("SELECT filename FROM videos WHERE id = ? AND user_id = ?", (video_id, user_id)).fetchone()
        if video:
            filename = video[0]
            full_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(full_path):
                os.remove(full_path)
            conn.execute("DELETE FROM videos WHERE id = ? AND user_id = ?", (video_id, user_id))

# --------- Routes ---------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register.html", response_class=HTMLResponse)
async def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login.html", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/rag.html", response_class=HTMLResponse)
async def rag_ui(request: Request, username: Optional[str] = Cookie(None)):
    if not username:
        return RedirectResponse("/login.html", status_code=303)
    return templates.TemplateResponse("rag.html", {"request": request, "username": username})

@app.get("/profile.html", response_class=HTMLResponse)
async def profile(request: Request, username: Optional[str] = Cookie(None)):
    if not username:
        return RedirectResponse("/login.html", status_code=303)
    user = get_user_by_username(username)
    if not user:
        return RedirectResponse("/login.html", status_code=303)
    videos = get_videos_by_user(user[0])
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": {
            "first_name": user[1],
            "last_name": user[2],
            "username": user[3]
        },
        "videos": [{"id": v[0], "url": f"/uploads/{v[1]}", "query": v[2]} for v in videos]
    })

from fastapi import Form

@app.post("/delete-video")
async def delete_video(video_id: int = Form(...), username: Optional[str] = Cookie(None)):
    if not username:
        return RedirectResponse("/login.html", status_code=303)

    user = get_user_by_username(username)
    if not user:
        return RedirectResponse("/login.html", status_code=303)

    # Get video filename by ID (with user verification)
    with sqlite3.connect(DB_PATH) as conn:
        video = conn.execute("SELECT filename FROM videos WHERE id = ? AND user_id = ?", (video_id, user[0])).fetchone()
        if video:
            file_path = os.path.join(UPLOAD_FOLDER, video[0])
            if os.path.exists(file_path):
                os.remove(file_path)
            conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    
    return RedirectResponse("/profile.html", status_code=303)


@app.post("/logout")
async def logout(response: Response):
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("username")
    return response

@app.post("/register")
async def register_user(first_name: str = Form(...), last_name: str = Form(...), username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    if password != confirm_password:
        return RedirectResponse("/register.html?error=PasswordMismatch", status_code=303)
    if get_user_by_username(username):
        return RedirectResponse("/register.html?error=UsernameTaken", status_code=303)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO users (first_name, last_name, username, password) VALUES (?, ?, ?, ?)",
                     (first_name, last_name, username, hash_password(password)))
    return RedirectResponse("/login.html?success=AccountCreated", status_code=302)

@app.post("/login")
async def login_user(response: Response, username: str = Form(...), password: str = Form(...)):
    user = get_user_by_username(username)
    if not user or user[4] != hash_password(password):
        return RedirectResponse("/login.html?error=InvalidCredentials", status_code=303)
    response = RedirectResponse("/rag.html", status_code=302)
    response.set_cookie("username", username)
    return response

@app.post("/generate")
async def generate_video(background_tasks: BackgroundTasks, request: Request, source_image: UploadFile = File(...), rag_document: UploadFile = File(...), rag_query: str = Form(...), enhancer: str = Form(""), reference_audio: UploadFile = File(None), username: Optional[str] = Cookie(None)):
    if not username:
        return JSONResponse(status_code=403, content={"error": "Not logged in"})
    user = get_user_by_username(username)
    if not user:
        return JSONResponse(status_code=403, content={"error": "User not found"})
    job_id = str(uuid.uuid4())
    video_status[job_id] = {"status": "pending", "url": None}

    temp_dir = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)

    def save_file(upload: UploadFile, name: str):
        ext = os.path.splitext(upload.filename)[1]
        path = os.path.join(temp_dir, name + ext)
        with open(path, "wb") as f:
            f.write(upload.file.read())
        return path

    image_path = save_file(source_image, "image")
    pdf_path = save_file(rag_document, "doc")
    audio_path = save_file(reference_audio, "audio") if reference_audio else None

    background_tasks.add_task(
        process_video_job,
        job_id,
        user[0],
        image_path,
        pdf_path,
        rag_query,
        enhancer,
        audio_path
    )
    return {"job_id": job_id}

def process_video_job(job_id, user_id, image_path, pdf_path, rag_query, enhancer, audio_path):
    try:
        temp_dir = os.path.dirname(image_path)
        args = [
            r"D:\\avatar_speech\\sadenv\\Scripts\\python.exe", "inference3.py",
            "--source_image", image_path,
            "--rag_query", rag_query,
            "--rag_document", pdf_path,
            "--source_lang", "en", "--target_lang", "en",
            "--result_dir", temp_dir
        ]
        if audio_path:
            args += ["--reference_audio", audio_path]
        if enhancer:
            args += ["--enhancer", enhancer]

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(f"[{job_id}] 🔧", output.strip())

        if process.poll() != 0:
            video_status[job_id] = {"status": "error", "url": None}
            return

        video_file = next((f for f in os.listdir(temp_dir) if f.endswith(".mp4")), None)
        if not video_file:
            video_status[job_id] = {"status": "error", "url": None}
            return

        full_path = os.path.join(temp_dir, video_file)
        rel_url = os.path.relpath(full_path, UPLOAD_FOLDER).replace("\\", "/")
        save_video_for_user(user_id, rel_url, rag_query)
        video_status[job_id] = {"status": "completed", "url": f"/uploads/{rel_url}"}

    except Exception as e:
        print(f"[{job_id}] ❌ Error:", e)
        video_status[job_id] = {"status": "error", "url": None}

@app.get("/status/{job_id}")
async def check_status(job_id: str):
    if job_id not in video_status:
        return {"status": "unknown"}
    return video_status[job_id]