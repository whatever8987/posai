"""
Complete training script for Vanna AI with Ollama (Local LLM)
This script uses Ollama for local, private, and free AI inference.

Prerequisites:
1. Install Ollama: https://ollama.com
2. Pull a model: ollama pull llama3.1
3. Install packages: pip install vanna ollama chromadb

Usage:
    python train_nail_salon_ollama.py
"""

import json
import os
from typing import Optional

# Import Vanna components
try:
    from vanna.ollama import Ollama
    from vanna.chromadb import ChromaDB_VectorStore
except ImportError:
    print("❌ Error: Required packages not installed")
    print("Please run: pip install vanna ollama chromadb")
    exit(1)


class NailSalonVanna(ChromaDB_VectorStore, Ollama):
    """Custom Vanna class for Nail Salon POS using Ollama"""
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


def test_ollama_connection(model: str = "qwen2.5:7b") -> bool:
    """Test if Ollama is running and model is available"""
    try:
        import ollama
        
        print("🔍 Testing Ollama connection...")
        
        # Check if Ollama service is running
        try:
            models = ollama.list()
            print("✓ Ollama service is running")
        except Exception as e:
            print("❌ Ollama service is not running")
            print("Start it with: ollama serve")
            return False
        
        # Check if model exists
        model_names = [m['model'] for m in models.get('models', [])]
        full_model_name = model if ':' in model else f"{model}:latest"
        
        if full_model_name not in model_names:
            print(f"⚠️  Model '{model}' not found")
            print(f"Available models: {', '.join(model_names)}")
            print(f"\nDownload it with: ollama pull {model}")
            
            # Ask if user wants to download
            response = input(f"\nWould you like to download {model} now? (y/n): ")
            if response.lower() == 'y':
                print(f"📥 Downloading {model}... (this may take a few minutes)")
                ollama.pull(model)
                print(f"✓ {model} downloaded successfully")
            else:
                return False
        else:
            print(f"✓ Model '{model}' is available")
        
        # Test a simple query
        print("🧪 Testing model inference...")
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': 'Say "OK" if you can hear me'}]
        )
        print(f"✓ Model responded: {response['message']['content'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Ollama: {str(e)}")
        return False


def initialize_vanna(model: str = "llama3.1", optimize_for: str = "balanced") -> NailSalonVanna:
    """
    Initialize Vanna with Ollama
    
    Args:
        model: Ollama model to use (llama3.1, codellama, mistral, etc.)
        optimize_for: 'speed', 'accuracy', or 'balanced'
    
    Returns:
        Configured NailSalonVanna instance
    """
    
    # Configuration presets
    configs = {
        'speed': {
            'model': model,
            'ollama_host': 'http://localhost:11434',
            'path': './chroma_db_nail_salon',
            'num_ctx': 2048,
            'keep_alive': '30m',  # Keep in memory for 30 minutes
            'options': {
                'temperature': 0.1,
                'num_predict': 500
            }
        },
        'accuracy': {
            'model': model,
            'ollama_host': 'http://localhost:11434',
            'path': './chroma_db_nail_salon',
            'num_ctx': 8192,
            'keep_alive': '5m',
            'options': {
                'temperature': 0.0,  # Most deterministic
                'top_p': 1.0
            }
        },
        'balanced': {
            'model': model,
            'ollama_host': 'http://localhost:11434',
            'path': './chroma_db_nail_salon',
            'num_ctx': 4096,
            'keep_alive': '5m',
            'options': {
                'temperature': 0.1,
                'top_p': 0.9,
                'top_k': 40
            }
        }
    }
    
    config = configs.get(optimize_for, configs['balanced'])
    
    print(f"\n🚀 Initializing Vanna with Ollama...")
    print(f"   Model: {model}")
    print(f"   Profile: {optimize_for}")
    print(f"   Context window: {config['num_ctx']}")
    
    try:
        vn = NailSalonVanna(config=config)
        print("✓ Vanna initialized successfully")
        return vn
    except Exception as e:
        print(f"❌ Error initializing Vanna: {str(e)}")
        raise


def train_database_schema(vn: NailSalonVanna) -> None:
    """Train Vanna with the nail salon database schema"""
    
    print("\n📊 Training database schema...")
    
    schemas = [
        {
            "name": "customers",
            "ddl": """
                CREATE TABLE customers (
                    customer_id INT PRIMARY KEY AUTO_INCREMENT,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    date_of_birth DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    INDEX idx_phone (phone),
                    INDEX idx_email (email)
                )
            """
        },
        {
            "name": "technicians",
            "ddl": """
                CREATE TABLE technicians (
                    technician_id INT PRIMARY KEY AUTO_INCREMENT,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    phone VARCHAR(20),
                    specialties TEXT,
                    hire_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    commission_rate DECIMAL(5,2) DEFAULT 50.00
                )
            """
        },
        {
            "name": "services",
            "ddl": """
                CREATE TABLE services (
                    service_id INT PRIMARY KEY AUTO_INCREMENT,
                    service_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    base_price DECIMAL(10,2) NOT NULL,
                    duration_minutes INT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_category (category)
                )
            """
        },
        {
            "name": "bookings",
            "ddl": """
                CREATE TABLE bookings (
                    booking_id INT PRIMARY KEY AUTO_INCREMENT,
                    customer_id INT NOT NULL,
                    technician_id INT NOT NULL,
                    booking_date DATE NOT NULL,
                    booking_time TIME NOT NULL,
                    status ENUM('scheduled', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
                    total_amount DECIMAL(10,2) NOT NULL,
                    discount_amount DECIMAL(10,2) DEFAULT 0,
                    tip_amount DECIMAL(10,2) DEFAULT 0,
                    payment_method VARCHAR(50),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                    FOREIGN KEY (technician_id) REFERENCES technicians(technician_id),
                    INDEX idx_booking_date (booking_date),
                    INDEX idx_status (status)
                )
            """
        },
        {
            "name": "booking_services",
            "ddl": """
                CREATE TABLE booking_services (
                    booking_service_id INT PRIMARY KEY AUTO_INCREMENT,
                    booking_id INT NOT NULL,
                    service_id INT NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
                    FOREIGN KEY (service_id) REFERENCES services(service_id)
                )
            """
        },
        {
            "name": "products",
            "ddl": """
                CREATE TABLE products (
                    product_id INT PRIMARY KEY AUTO_INCREMENT,
                    product_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50),
                    unit_price DECIMAL(10,2) NOT NULL,
                    current_stock INT DEFAULT 0,
                    min_stock_level INT DEFAULT 10,
                    supplier VARCHAR(100)
                )
            """
        },
        {
            "name": "product_sales",
            "ddl": """
                CREATE TABLE product_sales (
                    sale_id INT PRIMARY KEY AUTO_INCREMENT,
                    booking_id INT,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10,2) NOT NULL,
                    total_price DECIMAL(10,2) NOT NULL,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """
        }
    ]
    
    for schema in schemas:
        vn.train(ddl=schema["ddl"])
        print(f"  ✓ Trained table: {schema['name']}")


def train_business_documentation(vn: NailSalonVanna) -> None:
    """Train Vanna with business-specific terminology and rules"""
    
    print("\n📚 Training business documentation...")
    
    documentation = [
        {
            "name": "Service Categories",
            "content": """
                Service Categories in Nail Salon:
                - Manicure: Basic nail care and polish for hands
                - Pedicure: Basic nail care and polish for feet  
                - Gel/Shellac: Long-lasting gel polish
                - Acrylic/Extensions: Artificial nail enhancements
                - Nail Art: Custom designs and decorations
                - Spa Services: Premium treatments with massage
            """
        },
        {
            "name": "Booking Status & Revenue Rules",
            "content": """
                CRITICAL RULES:
                - Booking status values: 'scheduled', 'completed', 'cancelled', 'no_show'
                - ONLY count bookings with status='completed' for revenue calculations
                - total_amount includes service fees but NOT tips
                - tip_amount is separate and goes to technician
                - Revenue = SUM(total_amount) WHERE status='completed'
            """
        },
        {
            "name": "Customer Segmentation",
            "content": """
                Customer Classifications:
                - New Customer: First booking within last 30 days
                - Regular Customer: 2+ visits in last 90 days  
                - VIP Customer: 10+ total visits OR $1000+ lifetime spend
                - Lapsed Customer: No visits in last 60 days
            """
        }
    ]
    
    for doc in documentation:
        vn.train(documentation=doc["content"])
        print(f"  ✓ Trained: {doc['name']}")


def train_sql_examples(vn: NailSalonVanna, json_file: Optional[str] = None) -> None:
    """Train Vanna with SQL question-answer pairs"""
    
    print("\n💡 Training SQL examples...")
    
    if json_file and os.path.exists(json_file):
        with open(json_file, 'r') as f:
            examples = json.load(f)
        
        for i, example in enumerate(examples, 1):
            vn.train(
                question=example['question'],
                sql=example['answer']
            )
            if i % 5 == 0:
                print(f"  ✓ Trained {i}/{len(examples)} examples...")
        
        print(f"  ✓ Trained all {len(examples)} examples")
    else:
        print("  ! JSON file not found, skipping example training")


def test_trained_model(vn: NailSalonVanna) -> None:
    """Test the trained model with sample questions"""
    
    print("\n🧪 Testing trained model...")
    
    test_questions = [
        "What are our top 5 customers by spending?",
        "How much revenue did we make this month?",
        "Which technician has the most bookings this week?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n  Test {i}/{len(test_questions)}")
        print(f"  Question: {question}")
        try:
            sql = vn.generate_sql(question)
            # Show first 150 characters of SQL
            sql_preview = sql.replace('\n', ' ').strip()
            if len(sql_preview) > 150:
                sql_preview = sql_preview[:150] + "..."
            print(f"  Generated: {sql_preview}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


def connect_to_database(vn: NailSalonVanna, db_config: dict) -> None:
    """Connect Vanna to your database"""
    
    db_type = db_config.get('type', 'mysql')
    
    print(f"\n🔌 Connecting to {db_type} database...")
    
    try:
        if db_type == 'mysql':
            vn.connect_to_mysql(
                host=db_config.get('host', 'localhost'),
                dbname=db_config.get('dbname', 'nail_salon_pos'),
                user=db_config.get('user'),
                password=db_config.get('password'),
                port=db_config.get('port', 3306)
            )
        elif db_type == 'postgres':
            vn.connect_to_postgres(
                host=db_config.get('host', 'localhost'),
                dbname=db_config.get('dbname', 'nail_salon_pos'),
                user=db_config.get('user'),
                password=db_config.get('password'),
                port=db_config.get('port', 5432)
            )
        elif db_type == 'sqlite':
            vn.connect_to_sqlite(db_config.get('path', 'nail_salon_pos.db'))
        
        print(f"✓ Connected to {db_type} database")
    except Exception as e:
        print(f"⚠️  Could not connect to database: {str(e)}")
        print("   Continuing without database connection...")


def main():
    """Main training workflow"""
    
    print("=" * 70)
    print("  Vanna AI Training: Nail Salon POS System (with Ollama)")
    print("=" * 70)
    
    # Configuration
    MODEL = "qwen2.5:7b"  # Options: llama3.1, llama3.2, codellama, mistral, qwen2.5:7b
    OPTIMIZE_FOR = "balanced"  # Options: speed, accuracy, balanced
    
    # Test Ollama connection first
    if not test_ollama_connection(MODEL):
        print("\n❌ Ollama setup incomplete. Please fix the issues above and try again.")
        return
    
    print("\n" + "=" * 70)
    
    # Initialize Vanna
    vn = initialize_vanna(model=MODEL, optimize_for=OPTIMIZE_FOR)
    
    # Optional: Connect to database
    # Uncomment and configure if you have a database
    # db_config = {
    #     'type': 'mysql',
    #     'host': 'localhost',
    #     'dbname': 'nail_salon_pos',
    #     'user': 'root',
    #     'password': 'your_password'
    # }
    # connect_to_database(vn, db_config)
    
    # Training steps
    train_database_schema(vn)
    train_business_documentation(vn)
    
    # Load SQL examples
    json_file = os.path.join(os.path.dirname(__file__), 'questions.json')
    train_sql_examples(vn, json_file)
    
    # Test the model
    test_trained_model(vn)
    
    print("\n" + "=" * 70)
    print("✅ Training complete!")
    print("=" * 70)
    print("\n💡 Next steps:")
    print("  1. Try: vn.generate_sql('Your question here')")
    print("  2. Or: vn.ask('Your question here')")
    print("  3. Build a dashboard with Streamlit or Flask")
    print("\n📖 See OLLAMA_SETUP.md for more details")
    print("\n🎯 Your Vanna instance is ready to use!")
    

if __name__ == "__main__":
    main()

