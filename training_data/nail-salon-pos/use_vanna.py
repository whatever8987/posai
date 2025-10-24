"""
Use your trained Vanna model to ask questions about your nail salon
Run this after training is complete!

Usage:
    python use_vanna.py
"""

from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore


class NailSalonVanna(ChromaDB_VectorStore, Ollama):
    """Custom Vanna class for Nail Salon POS"""
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


def initialize_trained_vanna():
    """Initialize Vanna with your trained model"""
    
    print("🚀 Loading your trained Vanna model...")
    
    vn = NailSalonVanna(config={
        'model': 'qwen2.5:7b',
        'num_ctx': 4096,
        'keep_alive': '30m',  # Keep in memory for 30 minutes
        'path': './chroma_db_nail_salon',  # Your trained data
        'options': {
            'temperature': 0.1  # Low for consistent SQL
        }
    })
    
    print("✓ Model loaded successfully!")
    return vn


def connect_to_database(vn):
    """Connect to your actual database"""
    
    print("\n🔌 Connecting to database...")
    
    # OPTION 1: MySQL
    vn.connect_to_postgres(
        host='localhost',
        dbname='nail_salon_pos',
        user='postgres1',
        password='Hanoi.2389',
        port=5432
    )
    
    # OPTION 2: PostgreSQL
    # vn.connect_to_postgres(
    #     host='localhost',
    #     dbname='nail_salon_pos',
    #     user='postgres',
    #     password='your_password',
    #     port=5432
    # )
    
    # OPTION 3: SQLite
    # vn.connect_to_sqlite('nail_salon_pos.db')
    
    print("✓ Connected to database!")


def example_questions(vn):
    """Try some example questions"""
    
    print("\n" + "=" * 60)
    print("📊 Example Questions")
    print("=" * 60)
    
    questions = [
        "What are our top 10 customers by total spending?",
        "What is our total revenue for this month?",
        "Which technician has the most appointments this week?",
        "Show me customers who haven't visited in 60 days",
        "What are the 5 most popular services?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. {question}")
        print("-" * 60)
        
        try:
            # Generate SQL
            sql = vn.generate_sql(question)
            print(f"Generated SQL:\n{sql}")
            
            # Uncomment to run the SQL and show results:
            # df = vn.run_sql(sql)
            # print(f"\nResults:\n{df}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print()


def interactive_mode(vn):
    """Interactive Q&A mode"""
    
    print("\n" + "=" * 60)
    print("💬 Interactive Mode - Ask Your Own Questions!")
    print("=" * 60)
    print("\nType your questions about your nail salon.")
    print("Type 'quit', 'exit', or 'q' to stop.\n")
    
    while True:
        try:
            question = input("Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            print("\n🤔 Generating SQL...")
            sql = vn.generate_sql(question)
            
            print(f"\n📝 Generated SQL:")
            print("-" * 60)
            print(sql)
            print("-" * 60)
            
            # Ask if they want to run it
            run = input("\nRun this query? (y/n): ").lower()
            if run == 'y':
                try:
                    df = vn.run_sql(sql)
                    print(f"\n📊 Results:")
                    print(df)
                except Exception as e:
                    print(f"❌ Error running query: {e}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


def daily_dashboard(vn):
    """Generate a daily dashboard report"""
    
    print("\n" + "=" * 60)
    print("📈 Daily Dashboard")
    print("=" * 60)
    
    dashboard_queries = [
        ("📅 Today's Appointments", "How many appointments do we have today?"),
        ("💰 Today's Revenue", "What is today's total revenue?"),
        ("👥 Today's Customers", "How many customers are we seeing today?"),
        ("⭐ Top Service Today", "What is our most booked service today?"),
        ("🔮 Tomorrow's Schedule", "How many appointments do we have tomorrow?")
    ]
    
    for title, question in dashboard_queries:
        print(f"\n{title}")
        print("-" * 40)
        try:
            sql = vn.generate_sql(question)
            # Uncomment to run:
            # df = vn.run_sql(sql)
            # print(df)
            print(f"SQL: {sql[:80]}...")
        except Exception as e:
            print(f"Error: {e}")


def save_sql_for_later(vn, question):
    """Save generated SQL to a file for later use"""
    
    sql = vn.generate_sql(question)
    
    # Save to file
    filename = f"generated_sql_{question[:30].replace(' ', '_')}.sql"
    with open(filename, 'w') as f:
        f.write(f"-- Question: {question}\n")
        f.write(f"-- Generated by Vanna AI\n\n")
        f.write(sql)
    
    print(f"✓ SQL saved to {filename}")
    return sql


def main():
    """Main function"""
    
    print("=" * 60)
    print("  💅 Nail Salon AI Assistant")
    print("  Powered by Vanna + Ollama")
    print("=" * 60)
    
    # Initialize
    vn = initialize_trained_vanna()
    
    # Connect to database
    connect_to_database(vn)
    
    # Choose what to do
    print("\n📋 What would you like to do?")
    print("1. See example questions")
    print("2. Interactive mode (ask your own questions)")
    print("3. Generate daily dashboard")
    print("4. Just generate SQL (no database needed)")
    
    choice = input("\nYour choice (1-4): ").strip()
    
    if choice == '1':
        example_questions(vn)
    elif choice == '2':
        # Database already connected above
        interactive_mode(vn)
    elif choice == '3':
        daily_dashboard(vn)
    elif choice == '4':
        print("\n💡 Enter your question:")
        question = input("Question: ").strip()
        if question:
            print(f"\n📝 Generated SQL:")
            sql = vn.generate_sql(question)
            print(sql)
    else:
        print("\n❌ Invalid choice. Running example questions...")
        example_questions(vn)
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)
    print("\n💡 Tips:")
    print("  - To use with your database, uncomment connect_to_database()")
    print("  - To run SQL queries, uncomment vn.run_sql()")
    print("  - Build a Streamlit app for a nice UI!")


if __name__ == "__main__":
    main()

