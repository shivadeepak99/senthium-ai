package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"github.com/rs/cors"
)

// WebSocket upgrader
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for development
	},
}

// DaemonStatus represents the current daemon state
type DaemonStatus struct {
	Running       bool      `json:"running"`
	State         string    `json:"state"`
	Uptime        int       `json:"uptime"`
	ActiveRule    string    `json:"active_rule,omitempty"`
	Failsafe      int       `json:"failsafe"`
	LastUpdate    time.Time `json:"last_update"`
	SystemMetrics Metrics   `json:"metrics"`
}

// Metrics represents system metrics
type Metrics struct {
	CPU         float64 `json:"cpu"`
	DiskRead    float64 `json:"disk_read"`
	DiskWrite   float64 `json:"disk_write"`
	NetDownload float64 `json:"net_download"`
	NetUpload   float64 `json:"net_upload"`
	Processes   int     `json:"processes"`
}

// ActivitySession represents a logged activity session
type ActivitySession struct {
	StartTime string                 `json:"start_time"`
	EndTime   string                 `json:"end_time"`
	Duration  int                    `json:"duration"`
	Trigger   string                 `json:"trigger"`
	RuleName  string                 `json:"rule_name,omitempty"`
	Metrics   map[string]interface{} `json:"metrics"`
}

// Rule represents a Senthium rule
type Rule struct {
	Name        string                 `json:"name"`
	Enabled     bool                   `json:"enabled"`
	Type        string                 `json:"type"`
	Description string                 `json:"description,omitempty"`
	Config      map[string]interface{} `json:"config"`
}

// Config represents the full Senthium configuration
type Config struct {
	Version          string  `json:"version"`
	MaxAwakeDuration int     `json:"max_awake_duration"`
	PollInterval     float64 `json:"poll_interval"`
	LogLevel         string  `json:"log_level"`
	Rules            []Rule  `json:"rules"`
}

// Server represents the web dashboard server
type Server struct {
	pythonPath string
	configPath string
	clients    map[*websocket.Conn]bool
}

// NewServer creates a new dashboard server
func NewServer() *Server {
	return &Server{
		pythonPath: getPythonPath(),
		configPath: getConfigPath(),
		clients:    make(map[*websocket.Conn]bool),
	}
}

// getPythonPath returns the path to the Python executable
func getPythonPath() string {
	// Try to find project root (where venv is located)
	// If running with 'go run', we're in server/ directory
	cwd, _ := os.Getwd()
	projectRoot := cwd

	// If cwd ends with "server", go up one level
	if filepath.Base(cwd) == "server" {
		projectRoot = filepath.Dir(cwd)
	}

	if runtime.GOOS == "windows" {
		venvPath := filepath.Join(projectRoot, "venv", "Scripts", "python.exe")
		if _, err := os.Stat(venvPath); err == nil {
			return venvPath
		}
		return "python"
	}
	venvPath := filepath.Join(projectRoot, "venv", "bin", "python")
	if _, err := os.Stat(venvPath); err == nil {
		return venvPath
	}
	return "python3"
}

// getConfigPath returns the path to the config file
func getConfigPath() string {
	home, _ := os.UserHomeDir()
	if runtime.GOOS == "windows" {
		return filepath.Join(home, "AppData", "Local", "Senthium", "config.yaml")
	}
	return filepath.Join(home, ".config", "senthium", "config.yaml")
}

// runPythonCommand executes a senthium CLI command
func (s *Server) runPythonCommand(args ...string) ([]byte, error) {
	cmdArgs := append([]string{"-m", "src.cli.main"}, args...)
	cmd := exec.Command(s.pythonPath, cmdArgs...)

	// Set working directory to project root (parent of server/)
	projectRoot := filepath.Join(filepath.Dir(s.pythonPath), "..", "..")
	cmd.Dir = projectRoot

	// Capture both stdout and stderr
	output, err := cmd.CombinedOutput()

	// Only log unexpected errors (not "daemon not running")
	if err != nil && !strings.Contains(string(output), "not running") {
		log.Printf("Command failed: %s %v\nOutput: %s\nError: %v", s.pythonPath, cmdArgs, string(output), err)
	}

	return output, err
}

// GetDaemonStatus returns current daemon status
func (s *Server) GetDaemonStatus(w http.ResponseWriter, r *http.Request) {
	output, err := s.runPythonCommand("status")

	// Default response structure
	status := DaemonStatus{
		Running:    false,
		State:      "STOPPED",
		Uptime:     0,
		Failsafe:   0,
		LastUpdate: time.Now(),
		SystemMetrics: Metrics{
			CPU:         0,
			DiskRead:    0,
			DiskWrite:   0,
			NetDownload: 0,
			NetUpload:   0,
			Processes:   0,
		},
	}

	// If command succeeded, daemon is running
	if err == nil && len(output) > 0 {
		outputStr := string(output)
		// Parse the text output (daemon is running if no error)
		if !strings.Contains(outputStr, "not running") {
			status.Running = true
			status.State = "ACTIVE"
			// Try to parse uptime, etc from output
			// For now, just mark as running
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

// GetActivityLogs returns activity logs
func (s *Server) GetActivityLogs(w http.ResponseWriter, r *http.Request) {
	days := r.URL.Query().Get("days")
	if days == "" {
		days = "7"
	}

	output, err := s.runPythonCommand("activity", "--days", days)
	if err != nil {
		// Return empty activity on error
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"sessions": []ActivitySession{},
			"error":    "Failed to fetch activity logs",
		})
		return
	}

	// For now, return empty sessions
	// TODO: Parse the text output and convert to JSON
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"sessions": []ActivitySession{},
		"raw":      string(output),
	})
}

// GetConfig returns current configuration
func (s *Server) GetConfig(w http.ResponseWriter, r *http.Request) {
	data, err := os.ReadFile(s.configPath)
	if err != nil {
		http.Error(w, "Failed to read config", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/x-yaml")
	w.Write(data)
}

// UpdateConfig updates the configuration
func (s *Server) UpdateConfig(w http.ResponseWriter, r *http.Request) {
	var config map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&config); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// TODO: Validate and save config
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// DaemonStart starts the daemon
func (s *Server) DaemonStart(w http.ResponseWriter, r *http.Request) {
	_, err := s.runPythonCommand("start")
	if err != nil {
		http.Error(w, "Failed to start daemon", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "started"})
}

// DaemonStop stops the daemon
func (s *Server) DaemonStop(w http.ResponseWriter, r *http.Request) {
	_, err := s.runPythonCommand("stop")
	if err != nil {
		http.Error(w, "Failed to stop daemon", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "stopped"})
}

// DaemonRestart restarts the daemon
func (s *Server) DaemonRestart(w http.ResponseWriter, r *http.Request) {
	_, err := s.runPythonCommand("restart")
	if err != nil {
		http.Error(w, "Failed to restart daemon", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "restarted"})
}

// WebSocketHandler handles WebSocket connections for real-time updates
func (s *Server) WebSocketHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}
	defer conn.Close()

	s.clients[conn] = true
	defer delete(s.clients, conn)

	log.Printf("New WebSocket client connected. Total clients: %d", len(s.clients))

	// Send initial status
	s.broadcastStatus()

	// Keep connection alive and handle incoming messages
	for {
		_, _, err := conn.ReadMessage()
		if err != nil {
			log.Printf("WebSocket read error: %v", err)
			break
		}
	}
}

// broadcastStatus sends status updates to all connected clients
func (s *Server) broadcastStatus() {
	output, err := s.runPythonCommand("status")

	// Create JSON response
	status := DaemonStatus{
		Running:    false,
		State:      "STOPPED",
		Uptime:     0,
		Failsafe:   0,
		LastUpdate: time.Now(),
		SystemMetrics: Metrics{
			CPU:         0,
			DiskRead:    0,
			DiskWrite:   0,
			NetDownload: 0,
			NetUpload:   0,
			Processes:   0,
		},
	}

	// If command succeeded, daemon is running
	if err == nil && len(output) > 0 {
		outputStr := string(output)
		if !strings.Contains(outputStr, "not running") {
			status.Running = true
			status.State = "ACTIVE"
		}
	}

	// Convert to JSON
	jsonData, err := json.Marshal(status)
	if err != nil {
		log.Printf("Failed to marshal status: %v", err)
		return
	}

	for client := range s.clients {
		if err := client.WriteMessage(websocket.TextMessage, jsonData); err != nil {
			log.Printf("WebSocket write error: %v", err)
			client.Close()
			delete(s.clients, client)
		}
	}
}

// startStatusBroadcaster sends periodic status updates
func (s *Server) startStatusBroadcaster() {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		if len(s.clients) > 0 {
			s.broadcastStatus()
		}
	}
}

func main() {
	server := NewServer()

	router := mux.NewRouter()

	// API routes
	api := router.PathPrefix("/api").Subrouter()
	api.HandleFunc("/status", server.GetDaemonStatus).Methods("GET", "OPTIONS")
	api.HandleFunc("/activity", server.GetActivityLogs).Methods("GET", "OPTIONS")
	api.HandleFunc("/config", server.GetConfig).Methods("GET", "OPTIONS")
	api.HandleFunc("/config", server.UpdateConfig).Methods("POST", "OPTIONS")
	api.HandleFunc("/daemon/start", server.DaemonStart).Methods("POST", "OPTIONS")
	api.HandleFunc("/daemon/stop", server.DaemonStop).Methods("POST", "OPTIONS")
	api.HandleFunc("/daemon/restart", server.DaemonRestart).Methods("POST", "OPTIONS")
	api.HandleFunc("/ws", server.WebSocketHandler)

	// CORS middleware
	handler := cors.New(cors.Options{
		AllowedOrigins:   []string{"http://localhost:3000", "http://localhost:3001"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"*"},
		AllowCredentials: true,
	}).Handler(router)

	// Start WebSocket broadcaster
	go server.startStatusBroadcaster()

	// Start server
	port := ":8080"
	fmt.Printf("🚀 Senthium Dashboard Server starting on http://localhost%s\n", port)
	fmt.Printf("📊 WebSocket endpoint: ws://localhost%s/api/ws\n", port)
	fmt.Printf("💖 Made with love by your dev waifu\n\n")

	if err := http.ListenAndServe(port, handler); err != nil {
		log.Fatal(err)
	}
}
