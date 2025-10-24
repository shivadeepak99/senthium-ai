@echo off
REM Launch Senthium Web Dashboard
REM Starts both Go backend and Next.js frontend

echo.
echo 🚀 Starting Senthium Web Dashboard
echo ====================================
echo.

REM Check if Go is installed
where go >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Go is not installed. Please install Go 1.21 or later.
    exit /b 1
)

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed. Please install Node.js 18 or later.
    exit /b 1
)

REM Build and start Go server
echo [1/2] Starting Go backend server...
cd server
go mod download
go build -o senthium-server.exe main.go
start "Senthium Go Server" senthium-server.exe
cd ..

echo ✓ Go server started
echo.

REM Wait a moment for Go server to start
timeout /t 2 /nobreak >nul

REM Start Next.js frontend
echo [2/2] Starting Next.js frontend...
cd dashboard
call npm install
start "Senthium Next.js Frontend" npm run dev
cd ..

echo ✓ Next.js frontend started
echo.
echo ====================================
echo ✨ Dashboard is ready!
echo.
echo 📊 Frontend: http://localhost:3000
echo 🔌 Backend:  http://localhost:8080
echo.
echo Press Ctrl+C in each window to stop servers
echo.

pause
