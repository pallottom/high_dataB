# Multi-Environment Setup Guide

## Overview
This project is configured to support 3 environments:
- **development**: Local development with debug mode on, SQL queries logged
- **tests**: Testing environment with optimized settings for test runs
- **operational**: Production environment with optimized performance and minimal logging

## How to Use

### 1. Select Environment
Set the `ENVIRONMENT` variable when running your application:

#### Windows (PowerShell)
```powershell
$env:ENVIRONMENT = "development"
python main.py

$env:ENVIRONMENT = "tests"
python -m pytest

$env:ENVIRONMENT = "operational"
python main.py
```

#### Windows (Command Prompt)
```cmd
set ENVIRONMENT=development
python main.py
```

#### Linux/Mac
```bash
export ENVIRONMENT=development
python main.py
```

### 2. Environment Variables (.env files)
Use the provided `.env.{environment}` files:
- `.env.development` - For local development
- `.env.tests` - For running tests
- `.env.operational` - For production (keep sensitive data secure!)

Or load them manually:
```bash
# PowerShell
Get-Content .env.development | foreach { $parts = $_ -split '='; if ($parts.length -eq 2) { [Environment]::SetEnvironmentVariable($parts[0], $parts[1]) } }
```

### 3. Configuration Hierarchy
Settings are loaded in this order (later overrides earlier):
1. `config.toml` - Base configuration for each environment
2. `.env` file or environment variables - Can override specific values
3. Environment variables - Highest priority

## Configuration Options Explained

### Development Environment
```toml
[development]
debug = true              # Enable debug mode
log_level = "DEBUG"       # Log all debug messages
echo = true               # Print SQL queries to console
pool_size = 5             # Small connection pool for dev
```

### Tests Environment
```toml
[tests]
debug = true              # Debug enabled for test analysis
log_level = "INFO"        # Less verbose than DEBUG
echo = false              # Don't clutter output with SQL
pool_size = 3             # Minimal pool for isolated tests
```

### Operational Environment
```toml
[operational]
debug = false             # No debug mode in production
log_level = "WARNING"     # Only log warnings and errors
echo = false              # No SQL logging
pool_size = 20            # Large pool for many concurrent connections
max_overflow = 30         # Handle traffic spikes
pool_timeout = 60         # Longer timeout for high-load scenarios
```

## Database Setup

For each environment, create the corresponding database:

```sql
-- Development
CREATE DATABASE hi_dataB_dev;

-- Tests
CREATE DATABASE hi_dataB_test;

-- Operational
CREATE DATABASE hi_dataB_prod;
```

Then update `config.toml` with your actual server addresses for each environment.

## Security Notes

⚠️ **Important**: 
- Never commit `.env` files with real passwords to version control
- Add `.env*` (except `.env.example`) to `.gitignore`
- For operational environment, use strong passwords and consider using secrets management systems
- Store production credentials separately, not in the repository

## Switching Environments in Code

```python
import os
from database import engine, ENVIRONMENT

print(f"Running in {ENVIRONMENT} environment")

# You can also check environment in your code:
if ENVIRONMENT == "development":
    # Enable debug features
    pass
elif ENVIRONMENT == "operational":
    # Production-only optimizations
    pass
```
