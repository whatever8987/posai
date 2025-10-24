#!/bin/bash
# Quick setup script for PostgreSQL database

echo "🗄️  Setting up nail_salon_pos database..."
echo ""

# Database credentials
DB_USER="postgres1"
DB_PASSWORD="Hanoi.2389"
DB_NAME="nail_salon_pos"

# Create database if it doesn't exist
echo "1. Creating database..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h localhost -c "CREATE DATABASE $DB_NAME;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "   ✓ Database created successfully"
else
    echo "   ⚠️  Database might already exist (this is okay)"
fi

# Import schema
echo ""
echo "2. Creating tables and importing sample data..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h localhost -d $DB_NAME -f sample_schema_postgres.sql

if [ $? -eq 0 ]; then
    echo "   ✓ Schema and data imported successfully"
else
    echo "   ❌ Error importing schema"
    exit 1
fi

echo ""
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "="
echo "✅ Database setup complete!"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "="
echo ""
echo "You can now run: python use_vanna.py"

