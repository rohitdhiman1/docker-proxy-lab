package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
	"github.com/rs/cors"
)

var (
	db          *sql.DB
	redisClient *redis.Client
	ctx         = context.Background()
)

type Order struct {
	ID         int       `json:"id"`
	UserID     int       `json:"user_id"`
	ProductID  int       `json:"product_id"`
	Quantity   int       `json:"quantity"`
	TotalPrice float64   `json:"total_price"`
	Status     string    `json:"status"`
	CreatedAt  time.Time `json:"created_at"`
}

type HealthStatus struct {
	Service   string    `json:"service"`
	Status    string    `json:"status"`
	Database  string    `json:"database"`
	Redis     string    `json:"redis"`
	Timestamp time.Time `json:"timestamp"`
}

type Stats struct {
	Service      string    `json:"service"`
	TotalOrders  int       `json:"total_orders"`
	TotalRevenue float64   `json:"total_revenue"`
	Timestamp    time.Time `json:"timestamp"`
}

func initDB() error {
	host := getEnv("DB_HOST", "postgres")
	dbName := getEnv("DB_NAME", "labdb")
	user := getEnv("DB_USER", "labuser")
	password := getEnv("DB_PASSWORD", "labpass")
	port := getEnv("DB_PORT", "5432")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbName)

	var err error
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		return err
	}

	// Test connection
	if err = db.Ping(); err != nil {
		return err
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	log.Println("Connected to PostgreSQL")
	return nil
}

func initRedis() {
	host := getEnv("REDIS_HOST", "redis")
	port := getEnv("REDIS_PORT", "6379")

	redisClient = redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%s", host, port),
	})

	_, err := redisClient.Ping(ctx).Result()
	if err != nil {
		log.Printf("Redis connection error: %v", err)
	} else {
		log.Println("Connected to Redis")
	}
}

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	health := HealthStatus{
		Service:   "order-service",
		Status:    "healthy",
		Timestamp: time.Now(),
	}

	// Check database
	if err := db.Ping(); err != nil {
		health.Database = "disconnected"
		health.Status = "unhealthy"
	} else {
		health.Database = "connected"
	}

	// Check Redis
	if _, err := redisClient.Ping(ctx).Result(); err != nil {
		health.Redis = "disconnected"
	} else {
		health.Redis = "connected"
	}

	statusCode := http.StatusOK
	if health.Status == "unhealthy" {
		statusCode = http.StatusServiceUnavailable
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(health)
}

func getOrdersHandler(w http.ResponseWriter, r *http.Request) {
	// Try cache first
	cacheKey := "orders:all"
	cachedData, err := redisClient.Get(ctx, cacheKey).Result()

	if err == nil {
		log.Println("Cache hit for orders")
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"orders":%s,"source":"cache"}`, cachedData)
		return
	}

	// Fetch from database
	rows, err := db.Query(`
		SELECT id, user_id, product_id, quantity, total_price, status, created_at 
		FROM orders 
		ORDER BY id DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var orders []Order
	for rows.Next() {
		var order Order
		if err := rows.Scan(&order.ID, &order.UserID, &order.ProductID, &order.Quantity,
			&order.TotalPrice, &order.Status, &order.CreatedAt); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		orders = append(orders, order)
	}

	// Cache for 60 seconds
	ordersJSON, _ := json.Marshal(orders)
	redisClient.Set(ctx, cacheKey, ordersJSON, 60*time.Second)
	log.Println("Cached orders data")

	response := map[string]interface{}{
		"orders": orders,
		"source": "database",
		"count":  len(orders),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func getOrderHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orderID, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid order ID", http.StatusBadRequest)
		return
	}

	// Try cache first
	cacheKey := fmt.Sprintf("order:%d", orderID)
	cachedData, err := redisClient.Get(ctx, cacheKey).Result()

	if err == nil {
		log.Printf("Cache hit for order %d", orderID)
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"order":%s,"source":"cache"}`, cachedData)
		return
	}

	// Fetch from database
	var order Order
	err = db.QueryRow(`
		SELECT id, user_id, product_id, quantity, total_price, status, created_at 
		FROM orders 
		WHERE id = $1
	`, orderID).Scan(&order.ID, &order.UserID, &order.ProductID, &order.Quantity,
		&order.TotalPrice, &order.Status, &order.CreatedAt)

	if err == sql.ErrNoRows {
		http.Error(w, "Order not found", http.StatusNotFound)
		return
	} else if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Cache for 5 minutes
	orderJSON, _ := json.Marshal(order)
	redisClient.Set(ctx, cacheKey, orderJSON, 5*time.Minute)
	log.Printf("Cached order %d data", orderID)

	response := map[string]interface{}{
		"order":  order,
		"source": "database",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func createOrderHandler(w http.ResponseWriter, r *http.Request) {
	var order Order
	if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if order.UserID == 0 || order.ProductID == 0 || order.Quantity == 0 {
		http.Error(w, "User ID, Product ID, and Quantity are required", http.StatusBadRequest)
		return
	}

	// Default status if not provided
	if order.Status == "" {
		order.Status = "pending"
	}

	err := db.QueryRow(`
		INSERT INTO orders (user_id, product_id, quantity, total_price, status) 
		VALUES ($1, $2, $3, $4, $5) 
		RETURNING id, created_at
	`, order.UserID, order.ProductID, order.Quantity, order.TotalPrice, order.Status).Scan(&order.ID, &order.CreatedAt)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Invalidate cache
	redisClient.Del(ctx, "orders:all")
	log.Println("Invalidated orders cache")

	response := map[string]interface{}{
		"order":   order,
		"message": "Order created successfully",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(response)
}

func updateOrderStatusHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orderID, err := strconv.Atoi(vars["id"])
	if err != nil {
		http.Error(w, "Invalid order ID", http.StatusBadRequest)
		return
	}

	var data map[string]string
	if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	status, ok := data["status"]
	if !ok {
		http.Error(w, "Status is required", http.StatusBadRequest)
		return
	}

	var order Order
	err = db.QueryRow(`
		UPDATE orders 
		SET status = $1 
		WHERE id = $2 
		RETURNING id, user_id, product_id, quantity, total_price, status, created_at
	`, status, orderID).Scan(&order.ID, &order.UserID, &order.ProductID, &order.Quantity,
		&order.TotalPrice, &order.Status, &order.CreatedAt)

	if err == sql.ErrNoRows {
		http.Error(w, "Order not found", http.StatusNotFound)
		return
	} else if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Invalidate caches
	redisClient.Del(ctx, "orders:all", fmt.Sprintf("order:%d", orderID))
	log.Printf("Invalidated cache for order %d", orderID)

	response := map[string]interface{}{
		"order":   order,
		"message": "Order status updated successfully",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func getStatsHandler(w http.ResponseWriter, r *http.Request) {
	var stats Stats
	stats.Service = "order-service"
	stats.Timestamp = time.Now()

	err := db.QueryRow(`
		SELECT 
			COUNT(*) as total_orders,
			COALESCE(SUM(total_price), 0) as total_revenue
		FROM orders
	`).Scan(&stats.TotalOrders, &stats.TotalRevenue)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"service": "Order Service",
		"version": "1.0.0",
		"endpoints": map[string]string{
			"health": "/health",
			"orders": "/api/v1/orders",
			"order":  "/api/v1/orders/<id>",
			"stats":  "/api/v1/stats",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	// Initialize database
	if err := initDB(); err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	// Initialize Redis
	initRedis()
	defer redisClient.Close()

	// Create router
	router := mux.NewRouter()

	// Routes
	router.HandleFunc("/", rootHandler).Methods("GET")
	router.HandleFunc("/health", healthHandler).Methods("GET")
	router.HandleFunc("/api/v1/orders", getOrdersHandler).Methods("GET")
	router.HandleFunc("/api/v1/orders/{id:[0-9]+}", getOrderHandler).Methods("GET")
	router.HandleFunc("/api/v1/orders", createOrderHandler).Methods("POST")
	router.HandleFunc("/api/v1/orders/{id:[0-9]+}/status", updateOrderStatusHandler).Methods("PATCH")
	router.HandleFunc("/api/v1/stats", getStatsHandler).Methods("GET")

	// CORS
	handler := cors.New(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"*"},
	}).Handler(router)

	// Server configuration
	port := getEnv("PORT", "8080")
	srv := &http.Server{
		Addr:         ":" + port,
		Handler:      handler,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Printf("Order Service running on port %s", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("Server error:", err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}

	log.Println("Server exited")
}
