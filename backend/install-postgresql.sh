#!/bin/bash

# PostgreSQL Installation & Setup Script for Ubuntu
# This script installs PostgreSQL, creates the database, user, and sets up connection pooling with PgBouncer
# 
# IMPORTANT: Create a .env file with your database credentials before running this script
# Copy from .env.example and fill in your values
# 
# Run: sudo bash install-postgresql.sh

set -e

echo "=== PostgreSQL Installation & Setup for Memory Game ==="
echo ""

# Check if .env file exists
if [ ! -f "./.env" ]; then
    echo -e "\033[0;31mERROR: .env file not found!\033[0m"
    echo "Please create a .env file first:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Load only DB_* variables from .env file
# Extract DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME safely
DB_USER=$(grep "^DB_USER" ./.env | cut -d '=' -f2 | xargs)
DB_PASSWORD=$(grep "^DB_PASSWORD" ./.env | cut -d '=' -f2 | xargs)
DB_HOST=$(grep "^DB_HOST" ./.env | cut -d '=' -f2 | xargs)
DB_PORT=$(grep "^DB_PORT" ./.env | cut -d '=' -f2 | xargs)
DB_NAME=$(grep "^DB_NAME" ./.env | cut -d '=' -f2 | xargs)

# Set defaults if not found
DB_USER=${DB_USER:-memory_game_user}
DB_PASSWORD=${DB_PASSWORD:-password}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-6432}
DB_NAME=${DB_NAME:-memory_game_db}

# Validate required variables
if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo -e "\033[0;31mERROR: DB_USER and DB_PASSWORD must be set in .env file!\033[0m"
    exit 1
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configuration from .env:${NC}"
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo "PostgreSQL Port: 5432"
echo "PgBouncer Port: $DB_PORT"
echo ""
echo -e "${YELLOW}WARNING: Make sure DB_PASSWORD is set to a strong password!${NC}"
echo ""
read -p "Continue with installation? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Installation cancelled."
    exit 1
fi
read -p "Continue with installation? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Installation cancelled."
    exit 1
fi

# Update system packages
echo -e "${GREEN}[1/6] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install PostgreSQL
echo -e "${GREEN}[2/6] Installing PostgreSQL...${NC}"
apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL service
echo -e "${GREEN}[3/6] Starting PostgreSQL service...${NC}"
systemctl start postgresql
systemctl enable postgresql

# Create database and user
echo -e "${GREEN}[4/6] Creating database and user...${NC}"
sudo -u postgres psql <<EOSQL
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET default_transaction_deferrable TO on;
ALTER ROLE $DB_USER SET default_transaction_deferrable TO on;
ALTER ROLE $DB_USER SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $DB_USER;
EOSQL

# Install PgBouncer (connection pooling)
echo -e "${GREEN}[5/6] Installing PgBouncer for connection pooling...${NC}"
apt-get install -y pgbouncer

# Configure PgBouncer
echo -e "${GREEN}[6/6] Configuring PgBouncer...${NC}"
cat > /etc/pgbouncer/pgbouncer.ini <<'EOF'
[databases]
memory_game_db = host=127.0.0.1 port=5432 user=memory_game_user password=TEMP_PASSWORD_REPLACE dbname=memory_game_db

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
max_user_connections = 100
server_lifetime = 3600
server_idle_timeout = 600
listen_port = 6432
listen_addr = 127.0.0.1
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
admin_users = postgres

[console]
admin_users = postgres
EOF

# Now replace the placeholder with actual password
sed -i "s/TEMP_PASSWORD_REPLACE/$DB_PASSWORD/g" /etc/pgbouncer/pgbouncer.ini
sed -i "s/memory_game_db/$DB_NAME/g" /etc/pgbouncer/pgbouncer.ini
sed -i "s/memory_game_user/$DB_USER/g" /etc/pgbouncer/pgbouncer.ini

# Create pgbouncer log directory
mkdir -p /var/log/pgbouncer
chown pgbouncer:pgbouncer /var/log/pgbouncer
chmod 755 /var/log/pgbouncer

# Create pgbouncer pid directory
mkdir -p /var/run/pgbouncer
chown pgbouncer:pgbouncer /var/run/pgbouncer
chmod 755 /var/run/pgbouncer

# Update pgbouncer config permissions
chown pgbouncer:pgbouncer /etc/pgbouncer/pgbouncer.ini
chmod 640 /etc/pgbouncer/pgbouncer.ini

# Restart PgBouncer
systemctl restart pgbouncer
systemctl enable pgbouncer

echo ""
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo ""
echo "PostgreSQL Connection Details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""
echo "PgBouncer Connection Details (use this in your app):"
echo "  Host: localhost"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""
echo "Next steps:"
echo "1. Ensure .env file is in your backend directory with DB_* variables"
echo "2. Run the migration script: python migrate_sqlite_to_postgresql.py"
echo "3. Update your application requirements: pip install -r requirements.txt"
echo "4. Copy .env.example to .env on your server"
echo "5. Restart your application"
echo ""
echo "PgBouncer is configured with:"
echo "  - Transaction pooling mode (best for web apps)"
echo "  - Max pool size: 25 connections per database"
echo "  - Connection timeout: 600 seconds"
echo ""
echo "To verify PgBouncer status:"
echo "  psql -h 127.0.0.1 -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo ""
