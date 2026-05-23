#first thing
for setup the python environment
python -m venv Jimatgo

for mac 
python3 -m venv Jimatgo

activate the virtual machine 
On Windows (PowerShell)
.\Jimatgo\Scripts\Activate.ps1

On Windows (Command Prompt)
.\Jimatgo\Scripts\activate.bat

On macOS/Linux
source Jimatgo/bin/activate

Set Up PostgreSQL Database

Create a new PostgreSQL database for the application:

- open postgres
- psql -U postgres
create database
- CREATE DATABASE JIMAT

Create a `.env` file in the project root directory with the following variables:
Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/jimat

Security
SECRET_KEY=your-secret-key-here-change-this-in-production

JWT Configuration
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

API Keys (Get these from their respective services)
GEMINI_API_KEY=your-gemini-api-key
SERPAPI_API_KEY=your-serpapi-api-key

run the backend 
uvicorn main:app --reload --host 0.0.0.0 --port 8000 (if u want to test it on phone)
uvicorn main:app --reload (want to test in only on chrome)



 
    
