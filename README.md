# 🚀 FastAPI Blog API

A high-performance **Blog Backend API** built with **FastAPI**, featuring authentication, CRUD operations, and scalable architecture. Designed as a foundation for an AI-driven blogging platform.

---

## 📌 Features

* 🔐 JWT Authentication (Login / Register)
* 📝 Blog CRUD (Create, Read, Update, Delete)
* 👤 User Management
* ⚡ FastAPI async performance
* 🗄️ SQLAlchemy ORM integration
* 🔒 Password hashing (bcrypt)
* 📦 Modular project structure

---

## 🏗️ Tech Stack

* **Backend:** FastAPI
* **Database:** SQLite / PostgreSQL (configurable)
* **ORM:** SQLAlchemy
* **Auth:** JWT (python-jose)
* **Hashing:** Passlib (bcrypt)
* **Server:** Uvicorn

---

## 📁 Project Structure

```
blog/
│── routers/        # API routes
│── models/         # Database models
│── schemas/        # Pydantic schemas
│── database/       # DB connection
│── hashing/        # Password hashing
│── token/          # JWT logic
│── main.py         # Entry point
```

---

## ⚙️ Installation

### 1. Clone the repo

```bash
git clone https://github.com/sriram020204/fastapi-blog.git
cd fastapi-blog
```

---

### 2. Create virtual environment

```bash
python -m venv blog-env
blog-env\Scripts\activate   # Windows
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
uvicorn blog.main:app --reload
```

App will be live at:
👉 http://127.0.0.1:8000

---

## 📚 API Documentation

FastAPI auto-generates docs:

* Swagger UI → http://127.0.0.1:8000/docs
* ReDoc → http://127.0.0.1:8000/redoc

---

## 🔐 Authentication Flow

1. Register user
2. Login → get JWT token
3. Use token in headers:

```
Authorization: Bearer <your_token>
```

---

## 🌱 Future Improvements

* 🤖 AI-generated blog content
* 💬 Multi-agent AI discussions
* 🧠 Topic-based AI channels
* 📊 Analytics dashboard
* 🌍 Deployment (Render / AWS)

---

## 🧑‍💻 Author

**Sriram Kumar**
GitHub: https://github.com/sriram020204

---

## 📄 License

This project is licensed under the **MIT License**.

---

## ⭐ Support

If you found this useful, consider giving it a ⭐ on GitHub!
