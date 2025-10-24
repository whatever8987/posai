"""
Simple Streamlit Dashboard for Nail Salon
Built with Vanna AI + Ollama

Installation:
    pip install streamlit plotly

Usage:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore


class NailSalonVanna(ChromaDB_VectorStore, Ollama):
    """Custom Vanna class for Nail Salon POS"""
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


@st.cache_resource
def get_vanna():
    """Initialize and cache Vanna instance"""
    vn = NailSalonVanna(config={
        'model': 'qwen2.5:7b',
        'num_ctx': 4096,
        'keep_alive': '30m',
        'path': './chroma_db_nail_salon',
        'options': {'temperature': 0.1}
    })
    
    # Connect to PostgreSQL database
    vn.connect_to_postgres(
        host='localhost',
        dbname='nail_salon_pos',
        user='postgres1',
        password='Hanoi.2389',
        port=5432
    )
    
    return vn


def main():
    # Page config
    st.set_page_config(
        page_title="Nail Salon Analytics",
        page_icon="💅",
        layout="wide"
    )
    
    # Header
    st.title("💅 Nail Salon Analytics Dashboard")
    st.markdown(f"**Powered by Vanna AI + Ollama (Local)** | {datetime.now().strftime('%B %d, %Y')}")
    
    # Initialize Vanna
    with st.spinner("Loading AI model..."):
        vn = get_vanna()
    
    # Sidebar
    st.sidebar.title("🎯 Quick Actions")
    
    # Quick questions
    st.sidebar.subheader("Common Questions")
    quick_questions = [
        "What is today's total revenue?",
        "Show top 10 customers by spending",
        "How many appointments today?",
        "Which technician has most bookings this week?",
        "What are our most popular services?",
        "Show customers who haven't visited in 60 days",
        "What is this month's revenue?",
        "Show tomorrow's appointments"
    ]
    
    selected_quick = st.sidebar.selectbox(
        "Choose a quick question:",
        [""] + quick_questions
    )
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["💬 Ask Questions", "📊 Dashboard", "📝 SQL Editor"])
    
    # Tab 1: Ask Questions
    with tab1:
        st.header("Ask Questions in Plain English")
        
        # Use selected quick question or let user type
        if selected_quick:
            question = selected_quick
        else:
            question = st.text_input(
                "What would you like to know about your nail salon?",
                placeholder="e.g., What are our top 5 customers this month?"
            )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            generate_btn = st.button("🤖 Generate SQL", type="primary")
        with col2:
            run_btn = st.button("▶️ Run Query", disabled=True)  # Enable after SQL generated
        
        if generate_btn and question:
            with st.spinner("🤔 AI is thinking..."):
                try:
                    # Generate SQL
                    sql = vn.generate_sql(question)
                    
                    # Show SQL
                    st.subheader("Generated SQL")
                    st.code(sql, language='sql')
                    
                    # Store in session state
                    st.session_state['last_sql'] = sql
                    st.session_state['last_question'] = question
                    
                    # Try to run it (if database connected)
                    try:
                        df = vn.run_sql(sql)
                        
                        st.subheader("Results")
                        st.dataframe(df, use_container_width=True)
                        
                        # Try to create a chart if applicable
                        if len(df.columns) == 2 and len(df) > 0:
                            st.subheader("Visualization")
                            st.bar_chart(df.set_index(df.columns[0]))
                        
                        # Download option
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Results (CSV)",
                            csv,
                            "results.csv",
                            "text/csv"
                        )
                        
                    except Exception as e:
                        st.warning(f"Could not run query: {str(e)}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Tab 2: Dashboard
    with tab2:
        st.header("Business Overview")
        
        dashboard_queries = {
            "Today's Revenue": "What is today's total revenue?",
            "Today's Appointments": "How many appointments do we have today?",
            "Top Customer": "Who is our top customer this month?",
            "Most Popular Service": "What is our most popular service this week?",
            "Tomorrow's Bookings": "How many appointments are scheduled tomorrow?"
        }
        
        if st.button("🔄 Refresh Dashboard"):
            with st.spinner("Loading dashboard..."):
                cols = st.columns(2)
                for i, (title, question) in enumerate(dashboard_queries.items()):
                    with cols[i % 2]:
                        with st.container():
                            st.subheader(title)
                            try:
                                sql = vn.generate_sql(question)
                                with st.expander("View SQL"):
                                    st.code(sql, language='sql')
                                
                                # Run the query
                                df = vn.run_sql(sql)
                                
                                # Display results
                                if df is not None and not df.empty:
                                    st.dataframe(df, use_container_width=True)
                                else:
                                    st.info("No data found")
                                
                            except Exception as e:
                                st.error(f"Error: {e}")
        else:
            st.info("👆 Click 'Refresh Dashboard' to generate reports")
    
    # Tab 3: SQL Editor
    with tab3:
        st.header("SQL Editor")
        st.markdown("Write or paste SQL directly")
        
        # Get last generated SQL if available
        default_sql = st.session_state.get('last_sql', '-- Write your SQL here')
        
        sql_input = st.text_area(
            "SQL Query",
            value=default_sql,
            height=200
        )
        
        if st.button("▶️ Execute SQL"):
            if sql_input and sql_input != '-- Write your SQL here':
                try:
                    df = vn.run_sql(sql_input)
                    st.success("✅ Query executed successfully")
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please enter a SQL query")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 Resources")
    st.sidebar.markdown("- [Vanna Docs](https://vanna.ai/docs/)")
    st.sidebar.markdown("- [Ollama](https://ollama.com)")
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Tip**: This runs 100% locally with no API costs!")


if __name__ == "__main__":
    main()

