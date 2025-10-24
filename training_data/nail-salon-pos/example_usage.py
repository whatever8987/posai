"""
Example usage of Vanna for Nail Salon POS
Shows both OpenAI and Ollama implementations
"""

# ============================================================================
# EXAMPLE 1: Using Ollama (Local, Free)
# ============================================================================

def example_ollama():
    """Example using Ollama for local, free AI"""
    
    print("=" * 60)
    print("Example 1: Using Ollama (Local, Free)")
    print("=" * 60)
    
    from vanna.ollama import Ollama
    from vanna.chromadb import ChromaDB_VectorStore
    
    class NailSalonVanna(ChromaDB_VectorStore, Ollama):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            Ollama.__init__(self, config=config)
    
    # Initialize with Ollama
    vn = NailSalonVanna(config={
        'model': 'llama3.1',  # Or: codellama, mistral, qwen2.5-coder
        'num_ctx': 4096,
        'keep_alive': '5m'
    })
    
    # Connect to database
    vn.connect_to_mysql(
        host='localhost',
        dbname='nail_salon_pos',
        user='root',
        password='password'
    )
    
    # Train (do this once)
    print("\n📚 Training...")
    vn.train(ddl="""
        CREATE TABLE bookings (
            booking_id INT PRIMARY KEY,
            customer_id INT,
            booking_date DATE,
            total_amount DECIMAL(10,2),
            status VARCHAR(20)
        )
    """)
    
    vn.train(
        question="What is today's revenue?",
        sql="SELECT SUM(total_amount) FROM bookings WHERE DATE(booking_date) = CURRENT_DATE AND status='completed'"
    )
    
    # Ask questions
    print("\n💬 Asking questions...")
    
    questions = [
        "What is our revenue for this month?",
        "Who are our top 5 customers?",
        "How many appointments do we have today?"
    ]
    
    for question in questions:
        print(f"\nQ: {question}")
        sql = vn.generate_sql(question)
        print(f"SQL: {sql[:100]}...")
        
        # Uncomment to run:
        # df = vn.run_sql(sql)
        # print(df)


# ============================================================================
# EXAMPLE 2: Using OpenAI (Cloud, Best Accuracy)
# ============================================================================

def example_openai():
    """Example using OpenAI for best accuracy"""
    
    print("\n" + "=" * 60)
    print("Example 2: Using OpenAI (Cloud, Best Accuracy)")
    print("=" * 60)
    
    import os
    from vanna.openai import OpenAI_Chat
    from vanna.chromadb import ChromaDB_VectorStore
    
    class NailSalonVanna(ChromaDB_VectorStore, OpenAI_Chat):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            OpenAI_Chat.__init__(self, config=config)
    
    # Initialize with OpenAI
    vn = NailSalonVanna(config={
        'api_key': os.environ.get('OPENAI_API_KEY'),
        'model': 'gpt-4'  # Or: gpt-3.5-turbo for cheaper/faster
    })
    
    # Connect to database
    vn.connect_to_mysql(
        host='localhost',
        dbname='nail_salon_pos',
        user='root',
        password='password'
    )
    
    # Train (same as Ollama)
    print("\n📚 Training...")
    vn.train(ddl="""
        CREATE TABLE bookings (
            booking_id INT PRIMARY KEY,
            customer_id INT,
            booking_date DATE,
            total_amount DECIMAL(10,2),
            status VARCHAR(20)
        )
    """)
    
    # Ask questions
    print("\n💬 Asking questions...")
    sql = vn.generate_sql("What is today's revenue?")
    print(f"Generated SQL: {sql}")


# ============================================================================
# EXAMPLE 3: Simple Interactive Session
# ============================================================================

def interactive_session():
    """Simple interactive Q&A session"""
    
    print("\n" + "=" * 60)
    print("Example 3: Interactive Session")
    print("=" * 60)
    
    from vanna.ollama import Ollama
    from vanna.chromadb import ChromaDB_VectorStore
    
    class MyVanna(ChromaDB_VectorStore, Ollama):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            Ollama.__init__(self, config=config)
    
    vn = MyVanna(config={'model': 'llama3.1'})
    
    # Assuming already trained and connected
    print("\nAsk questions about your nail salon!")
    print("Type 'quit' to exit\n")
    
    while True:
        question = input("Your question: ")
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        try:
            sql = vn.generate_sql(question)
            print(f"\nGenerated SQL:\n{sql}\n")
            
            # Uncomment to run:
            # df = vn.run_sql(sql)
            # print(df)
            # print()
        except Exception as e:
            print(f"Error: {e}\n")


# ============================================================================
# EXAMPLE 4: Common Business Questions
# ============================================================================

def common_questions_demo():
    """Demo of common nail salon business questions"""
    
    print("\n" + "=" * 60)
    print("Example 4: Common Business Questions")
    print("=" * 60)
    
    from vanna.ollama import Ollama
    from vanna.chromadb import ChromaDB_VectorStore
    
    class MyVanna(ChromaDB_VectorStore, Ollama):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            Ollama.__init__(self, config=config)
    
    vn = MyVanna(config={'model': 'llama3.1'})
    
    # Common nail salon questions
    questions = {
        "Revenue": [
            "What is our total revenue this month?",
            "What was yesterday's revenue?",
            "Compare this month's revenue to last month"
        ],
        "Customers": [
            "Who are our top 10 customers by spending?",
            "How many new customers this month?",
            "Which customers haven't visited in 60 days?"
        ],
        "Technicians": [
            "Which technician has the most appointments this week?",
            "Show each technician's revenue for this month",
            "What is the average tip per technician?"
        ],
        "Services": [
            "What are our 5 most popular services?",
            "Which service generates the most revenue?",
            "How many gel manicures did we do this week?"
        ],
        "Operations": [
            "How many appointments do we have tomorrow?",
            "What is our cancellation rate this month?",
            "Show me today's schedule"
        ]
    }
    
    for category, qs in questions.items():
        print(f"\n{category} Questions:")
        print("-" * 40)
        for q in qs:
            print(f"  • {q}")


# ============================================================================
# EXAMPLE 5: Building a Simple Dashboard
# ============================================================================

def dashboard_example():
    """Example of a simple text-based dashboard"""
    
    print("\n" + "=" * 60)
    print("Example 5: Simple Dashboard")
    print("=" * 60)
    
    from vanna.ollama import Ollama
    from vanna.chromadb import ChromaDB_VectorStore
    from datetime import datetime
    
    class MyVanna(ChromaDB_VectorStore, Ollama):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            Ollama.__init__(self, config=config)
    
    vn = MyVanna(config={'model': 'llama3.1'})
    
    # Connect to database
    # vn.connect_to_mysql(...)
    
    print(f"\n💅 Nail Salon Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    dashboard_queries = [
        ("Today's Revenue", "What is today's total revenue?"),
        ("Today's Appointments", "How many appointments do we have today?"),
        ("Top Customer", "Who is our top customer this month?"),
        ("Most Popular Service", "What is our most booked service today?"),
        ("Tomorrow's Schedule", "How many appointments are scheduled for tomorrow?")
    ]
    
    for title, question in dashboard_queries:
        print(f"\n{title}:")
        print("-" * 40)
        sql = vn.generate_sql(question)
        print(f"SQL: {sql[:80]}...")
        
        # Uncomment to run and display:
        # df = vn.run_sql(sql)
        # print(df)


# ============================================================================
# EXAMPLE 6: Comparison - Response Quality
# ============================================================================

def compare_models():
    """Compare different models' responses"""
    
    print("\n" + "=" * 60)
    print("Example 6: Comparing Different Models")
    print("=" * 60)
    
    from vanna.ollama import Ollama
    from vanna.chromadb import ChromaDB_VectorStore
    
    class MyVanna(ChromaDB_VectorStore, Ollama):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            Ollama.__init__(self, config=config)
    
    test_question = "What are the top 5 customers by total spending?"
    
    models = ['llama3.1', 'codellama', 'mistral']
    
    print(f"\nTest Question: {test_question}\n")
    
    for model in models:
        print(f"\n--- {model} ---")
        try:
            vn = MyVanna(config={'model': model})
            # Would need to train first in real use
            sql = vn.generate_sql(test_question)
            print(f"Generated: {sql[:100]}...")
        except Exception as e:
            print(f"Error with {model}: {e}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Vanna AI Examples for Nail Salon POS")
    print("=" * 60)
    
    print("\nAvailable examples:")
    print("1. Ollama (Local, Free)")
    print("2. OpenAI (Cloud, Best Accuracy)")
    print("3. Interactive Session")
    print("4. Common Business Questions")
    print("5. Simple Dashboard")
    print("6. Compare Models")
    
    choice = input("\nWhich example? (1-6, or 'all'): ")
    
    if choice == '1':
        example_ollama()
    elif choice == '2':
        example_openai()
    elif choice == '3':
        interactive_session()
    elif choice == '4':
        common_questions_demo()
    elif choice == '5':
        dashboard_example()
    elif choice == '6':
        compare_models()
    elif choice.lower() == 'all':
        common_questions_demo()
        dashboard_example()
    else:
        print("\nTo use these examples:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Pull a model: ollama pull llama3.1")
        print("3. Train your model: python train_nail_salon_ollama.py")
        print("4. Run this script: python example_usage.py")

