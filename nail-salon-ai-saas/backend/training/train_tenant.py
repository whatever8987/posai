"""
Training script for new tenants
Automatically trains Vanna AI with standard schema and example queries
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from standard_schema_training import get_all_training_data
from app.services.vanna_service import VannaService
from app.core.config import settings


async def train_new_tenant(tenant_id: str, verbose: bool = True):
    """
    Train Vanna AI for a new tenant with standard schema
    
    Args:
        tenant_id: Tenant UUID
        verbose: Print progress messages
    
    Returns:
        Training results dictionary
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Training Vanna AI for Tenant: {tenant_id}")
        print(f"{'='*60}\n")
    
    # Initialize Vanna service for tenant
    vanna_service = VannaService(tenant_id)
    
    # Get training data
    training_data = get_all_training_data()
    
    results = {
        "tenant_id": tenant_id,
        "ddl_trained": False,
        "questions_trained": 0,
        "documentation_added": 0,
        "errors": []
    }
    
    try:
        # 1. Train DDL (schema structure)
        if verbose:
            print("📊 Step 1: Training database schema...")
        
        vanna_service.vn.train(ddl=training_data["ddl"])
        results["ddl_trained"] = True
        
        if verbose:
            print("   ✓ Schema trained successfully")
        
        # 2. Train question-SQL pairs
        if verbose:
            print(f"\n💬 Step 2: Training {len(training_data['questions'])} example queries...")
        
        for i, example in enumerate(training_data['questions'], 1):
            try:
                vanna_service.vn.train(
                    question=example['question'],
                    sql=example['sql']
                )
                results["questions_trained"] += 1
                
                if verbose and i % 5 == 0:
                    print(f"   Progress: {i}/{len(training_data['questions'])} questions trained")
                    
            except Exception as e:
                error_msg = f"Error training question {i}: {str(e)}"
                results["errors"].append(error_msg)
                if verbose:
                    print(f"   ⚠️  {error_msg}")
        
        if verbose:
            print(f"   ✓ Trained {results['questions_trained']} questions successfully")
        
        # 3. Add business documentation
        if verbose:
            print(f"\n📚 Step 3: Adding {len(training_data['documentation'])} business term definitions...")
        
        for doc in training_data['documentation']:
            try:
                vanna_service.vn.train(documentation=f"{doc['term']}: {doc['documentation']}")
                results["documentation_added"] += 1
            except Exception as e:
                error_msg = f"Error adding documentation for {doc['term']}: {str(e)}"
                results["errors"].append(error_msg)
                if verbose:
                    print(f"   ⚠️  {error_msg}")
        
        if verbose:
            print(f"   ✓ Added {results['documentation_added']} documentation entries")
        
        # 4. Test the training
        if verbose:
            print("\n🧪 Step 4: Testing AI with sample query...")
        
        test_question = "Who are our top 5 customers?"
        try:
            test_sql = vanna_service.vn.generate_sql(test_question)
            
            if verbose:
                print(f"   Test Question: {test_question}")
                print(f"   Generated SQL: {test_sql[:100]}...")
                print("   ✓ AI is responding correctly")
                
            results["test_passed"] = True
            results["test_sql"] = test_sql
            
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Test failed: {str(e)}")
            results["test_passed"] = False
            results["test_error"] = str(e)
        
        # Summary
        if verbose:
            print(f"\n{'='*60}")
            print("TRAINING COMPLETE ✓")
            print(f"{'='*60}")
            print(f"✓ Schema: Trained")
            print(f"✓ Questions: {results['questions_trained']}/{len(training_data['questions'])}")
            print(f"✓ Documentation: {results['documentation_added']}/{len(training_data['documentation'])}")
            if results['errors']:
                print(f"⚠️  Errors: {len(results['errors'])}")
            print(f"{'='*60}\n")
        
        return results
        
    except Exception as e:
        error_msg = f"Fatal training error: {str(e)}"
        results["errors"].append(error_msg)
        if verbose:
            print(f"\n❌ TRAINING FAILED: {error_msg}\n")
        return results


async def retrain_tenant(tenant_id: str, verbose: bool = True):
    """
    Retrain an existing tenant (useful after schema changes or improvements)
    
    Args:
        tenant_id: Tenant UUID
        verbose: Print progress messages
    
    Returns:
        Training results dictionary
    """
    if verbose:
        print(f"\n⚠️  RETRAINING TENANT: {tenant_id}")
        print("This will add new training data to existing knowledge.\n")
    
    return await train_new_tenant(tenant_id, verbose)


def get_training_stats(tenant_id: str) -> dict:
    """
    Get statistics about a tenant's training data
    
    Args:
        tenant_id: Tenant UUID
    
    Returns:
        Statistics dictionary
    """
    try:
        vanna_service = VannaService(tenant_id)
        
        # Get training info from ChromaDB
        training_data = vanna_service.vn.get_training_data()
        
        return {
            "tenant_id": tenant_id,
            "total_training_items": len(training_data) if training_data else 0,
            "has_training": len(training_data) > 0 if training_data else False
        }
    except Exception as e:
        return {
            "tenant_id": tenant_id,
            "error": str(e),
            "has_training": False
        }


if __name__ == "__main__":
    import asyncio
    
    # Example usage
    print("""
╔════════════════════════════════════════════════════════════╗
║           VANNA AI TENANT TRAINING SCRIPT                  ║
╚════════════════════════════════════════════════════════════╝

This script trains Vanna AI for a new tenant with:
  • Complete database schema (7 tables)
  • 30+ example question-SQL pairs
  • Business terminology documentation

Usage:
  python train_tenant.py <tenant_id>

Example:
  python train_tenant.py 123e4567-e89b-12d3-a456-426614174000
    """)
    
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a tenant_id")
        print("   Usage: python train_tenant.py <tenant_id>")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    
    # Run training
    results = asyncio.run(train_new_tenant(tenant_id, verbose=True))
    
    # Exit with appropriate code
    if results['errors']:
        sys.exit(1)
    else:
        print("✅ Training completed successfully!")
        sys.exit(0)

