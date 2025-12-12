from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import secrets
from datebase import Database, get_db
from typing import Optional

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount(path="/static", app=StaticFiles(directory="static"), name="static")

# Для сессий
sessions = {}


def get_current_user(request: Request) -> Optional[dict]:
    """Получить текущего пользователя из сессии"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None


def require_auth(request: Request):
    """Проверка авторизации для защищенных страниц"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return user


# Главная страница (доступна без авторизации)
@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    user = get_current_user(request)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Басты бет",
        "user": user
    })


# Страница hope.html с данными из БД (требует авторизации)
@app.get("/hope", response_class=HTMLResponse)
def read_hope(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    # Получаем упражнения и советы из базы данных
    exercises = db.get_all_exercises()
    advice_list = db.get_all_advice()

    return templates.TemplateResponse("hope.html", {
        "request": request,
        "title": "Үміт бағы",
        "user": user,
        "exercises": exercises,
        "advice_list": advice_list
    })


# Страница упражнений (требует авторизации)
@app.get("/exercise", response_class=HTMLResponse)
def read_exercise(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    exercises = db.get_all_exercises()

    return templates.TemplateResponse("exercise.html", {
        "request": request,
        "title": "Жаттығулар",
        "user": user,
        "exercises": exercises
    })


# Страница конкретного упражнения (требует авторизации)
@app.get("/exercise/{exercise_id}", response_class=HTMLResponse)
def read_exercise_detail(request: Request, exercise_id: int, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    exercise = db.get_exercise_by_id(exercise_id)
    if not exercise:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Қате",
            "user": user,
            "error": "Жаттығу табылмады"
        })

    # Добавляем в историю просмотров
    if user:
        db.add_view_history(user["id"], "exercise", exercise_id, exercise["name"])

    return templates.TemplateResponse("exercise_detail.html", {
        "request": request,
        "title": exercise["name"],
        "user": user,
        "exercise": exercise
    })


# Страница советов (требует авторизации)
@app.get("/advice", response_class=HTMLResponse)
def read_advice(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    advice_list = db.get_all_advice()

    return templates.TemplateResponse("advice.html", {
        "request": request,
        "title": "Кеңес беру",
        "user": user,
        "advice_list": advice_list
    })


# Страница конкретного совета (требует авторизации)
@app.get("/advice/{advice_id}", response_class=HTMLResponse)
def read_advice_detail(request: Request, advice_id: int, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    advice = db.get_advice_by_id(advice_id)
    if not advice:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Қате",
            "user": user,
            "error": "Кеңес табылмады"
        })

    # Добавляем в историю просмотров
    if user:
        db.add_view_history(user["id"], "advice", advice_id, advice["name"])

    return templates.TemplateResponse("advice_detail.html", {
        "request": request,
        "title": advice["name"],
        "user": user,
        "advice": advice
    })


# Страница voices.html с комментариями (требует авторизации)
@app.get("/voices", response_class=HTMLResponse)
def read_voices(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    # Получаем все комментарии
    comments = db.get_all_comments()

    return templates.TemplateResponse("voices.html", {
        "request": request,
        "title": "Дауыстар алаңы",
        "user": user,
        "comments": comments
    })


# Добавление комментария
@app.post("/add_comment", response_class=HTMLResponse)
def add_comment(
        request: Request,
        first_name: str = Form(...),
        last_name: str = Form(...),
        comment: str = Form(...),
        db: Database = Depends(get_db)
):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    # Валидация данных
    if not first_name or not last_name or not comment:
        comments = db.get_all_comments()
        return templates.TemplateResponse("voices.html", {
            "request": request,
            "title": "Дауыстар алаңы",
            "user": user,
            "comments": comments,
            "error": "Барлық өрістерді толтырыңыз!"
        })

    # Сохраняем комментарий
    success = db.add_comment(user["id"], first_name, last_name, comment)

    if not success:
        comments = db.get_all_comments()
        return templates.TemplateResponse("voices.html", {
            "request": request,
            "title": "Дауыстар алаңы",
            "user": user,
            "comments": comments,
            "error": "Комментарий сақталмады. Өтінеміз, қайталаңыз."
        })

    # Возвращаемся на страницу с комментариями
    return RedirectResponse(url="/voices", status_code=302)


# Страница истории просмотров
@app.get("/history", response_class=HTMLResponse)
def read_history(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    # Получаем историю просмотров пользователя
    view_history = db.get_view_history(user["id"])

    return templates.TemplateResponse("history.html", {
        "request": request,
        "title": "Менің тарихым",
        "user": user,
        "view_history": view_history
    })


# Старые маршруты (требуют авторизации)
@app.get("/breathing", response_class=HTMLResponse)
def read_breathing(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    exercise = db.get_exercise_by_id(1)
    if user and exercise:
        db.add_view_history(user["id"], "exercise", 1, exercise["name"])

    return templates.TemplateResponse("breathing.html", {
        "request": request,
        "title": "Тыныс алу",
        "user": user,
        "exercise": exercise
    })


@app.get("/muscle", response_class=HTMLResponse)
def read_muscle(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    exercise = db.get_exercise_by_id(2)
    if user and exercise:
        db.add_view_history(user["id"], "exercise", 2, exercise["name"])

    return templates.TemplateResponse("muscle.html", {
        "request": request,
        "title": "Бұлшыкет",
        "user": user,
        "exercise": exercise
    })


@app.get("/meditation", response_class=HTMLResponse)
def read_meditation(request: Request, db: Database = Depends(get_db)):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    exercise = db.get_exercise_by_id(3)
    if user and exercise:
        db.add_view_history(user["id"], "exercise", 3, exercise["name"])

    return templates.TemplateResponse("meditation.html", {
        "request": request,
        "title": "Медитация",
        "user": user,
        "exercise": exercise
    })


# Авторизация (доступна без авторизации)
@app.post("/login", response_class=HTMLResponse)
def login_user(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Database = Depends(get_db)
):
    if db.verify_user(email, password):
        user = db.get_user_by_email(email)
        session_id = secrets.token_hex(16)
        sessions[session_id] = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Кіру",
            "error": "Қате электронды пошта немесе құпия сөз",
            "email": email
        })


@app.get("/logout")
def logout_user():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="session_id")
    return response


# Регистрация (доступна без авторизации)
@app.post("/register", response_class=HTMLResponse)
def register_user(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Database = Depends(get_db)
):
    if not name or not email or not password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "title": "Тіркелу",
            "error": "Барлық өрістер міндетті толтырылуы керек",
            "name": name,
            "email": email
        })

    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "title": "Тіркелу",
            "error": "Құпия сөз кемінде 6 таңбадан тұруы керек",
            "name": name,
            "email": email
        })

    success = db.insert_user(name, email, password)

    if success:
        return RedirectResponse(url="/login", status_code=302)
    else:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "title": "Тіркелу",
            "error": "Бұл электронды поштамен пайдаланушы тіркелген",
            "name": name,
            "email": email
        })


# Все остальные маршруты (требуют авторизации)
@app.get("/about", response_class=HTMLResponse)
def read_about(request: Request):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse("about.html", {
        "request": request,
        "title": "Біз туралы",
        "user": user
    })


# Страницы входа и регистрации (доступны без авторизации)
@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    user = get_current_user(request)
    # Если пользователь уже авторизован, перенаправляем на главную
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Кіру",
        "user": user
    })


@app.get("/register", response_class=HTMLResponse)
def read_register(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "title": "Тіркелу",
        "user": user
    })


# Остальные защищенные страницы
@app.get("/balance", response_class=HTMLResponse)
def read_balance(request: Request):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse("balance.html", {
        "request": request,
        "title": "Теңгерім",
        "user": user
    })


@app.get("/calm", response_class=HTMLResponse)
def read_calm(request: Request):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse("calm.html", {
        "request": request,
        "title": "Тыныштық",
        "user": user
    })


@app.get("/emotion", response_class=HTMLResponse)
def read_emotion(request: Request):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse("emotion.html", {
        "request": request,
        "title": "Эмоциялар",
        "user": user
    })


@app.get("/music", response_class=HTMLResponse)
def read_music(request: Request):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse("music.html", {
        "request": request,
        "title": "Музыка",
        "user": user
    })


@app.get("/selfsupport", response_class=HTMLResponse)
def read_selfsupport(request: Request):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse("selfsupport.html", {
        "request": request,
        "title": "Өзін-өзі қолдау",
        "user": user
    })


@app.get("/time", response_class=HTMLResponse)
def read_time(request: Request):
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse("time.html", {
        "request": request,
        "title": "Уақыт",
        "user": user
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)