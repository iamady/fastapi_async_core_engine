# Customer Orders & Recommendation Engine (CORE)

A FastAPI Async Customer Orders & AI based Recommendation Engine high-performance, production-ready FastAPI application demonstrating advanced async patterns, database management, and AI integration.

## 🚀 Features

- **Async-First Architecture**: Built with asyncio and async/await patterns
- **Modern Database**: SQLAlchemy 2.x with async support
- **Production-Ready**: Docker containerization with health checks
- **AI Integration**: OpenAI-compatible API with fallback mechanisms
- **Comprehensive Testing**: pytest-asyncio test suite
- **Data Seeding**: Faker-based mock data generation
- **Semantic Recommendations**: AI-powered product recommendations

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- OpenAI API key (optional, for AI features)

## 🛠️ Installation

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fastapi-async-core-engine
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Or build manually:**
   ```bash
   docker build -t fastapi-async-core-engine .
   docker run -p 8000:8000 fastapi-async-core-engine
   ```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test files
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing
```

## 📊 API Endpoints

### Health Check
- `GET /health` - Application health status

### Customers
- `POST /customers` - Create a new customer
- `GET /customers/{id}/history` - Get customer purchase history

### Orders
- `POST /orders` - Create a new order
- `GET /orders/{id}` - Get order details

### AI Recommendations
- `POST /customers/{id}/recommendations` - Get AI-powered recommendations

## 🤖 AI Integration

The application supports multiple AI providers:

### OpenAI (Default)
Set your OpenAI API key in `.env`:
```env
LLM_API_KEY=your_openai_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

### Ollama (Local AI)
For local AI models using Ollama:
```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3
```

### OpenRouter
For OpenRouter AI models:
```env
LLM_API_KEY=your_openrouter_api_key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=gpt-4
```

## 🌱 Data Seeding

Seed the database with realistic test data:

```bash
# Seed with 10 customers, products based on products.json , 5 orders / customer
python seed.py

# Reset database and reseed
python seed.py --reset

# TODO : Custom seeding
python seed.py --customers 50 --products 25 --orders 100
```

## 🐳 Docker Production Deployment

### Build Production Image
```bash
docker build -t fastapi-async-core-engine:production .
```

### Deploy with Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f core-app

# Scale application
docker-compose up -d --scale core-app=3

# Stop services
docker-compose down

# Run
docker run -p 8000:8000 --env-file .env core-app
```

### Production Environment Variables

Create a `.env.production` file:
```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/production_db

# AI Configuration
LLM_API_KEY=your_production_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# Security
SECRET_KEY=your_production_secret_key
DEBUG=False

# Logging
LOG_LEVEL=INFO
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./app.db` |
| `LLM_API_KEY` | AI provider API key | `None` |
| `LLM_BASE_URL` | AI provider base URL | `None` |
| `LLM_MODEL` | AI model to use | `None` |
| `DEBUG` | Enable debug mode | `True` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Database Configuration

The application supports multiple database backends:

- **SQLite** (Development): `sqlite+aiosqlite:///./app.db`
- **PostgreSQL** (Production): `postgresql://user:pass@host:port/db`
- **MySQL** (Production): `mysql+aiomysql://user:pass@host:port/db`

## 📈 Monitoring

### Health Checks
- Application health: `GET /health`
- Docker health check: Built into container

### Logging
Logs are automatically generated and can be viewed:
```bash
# Docker logs
docker-compose logs core-app

# Local development
tail -f logs/app.log
```

## 🚀 Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Configure proper database (PostgreSQL recommended)
- [ ] Set up SSL/TLS termination
- [ ] Configure logging and monitoring
- [ ] Set up backup strategies
- [ ] Configure firewall and security groups
- [ ] Set up CI/CD pipeline

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
