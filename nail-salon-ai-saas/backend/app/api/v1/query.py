"""
Natural language query endpoints
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from ...core.database import get_db, TenantDatabase
from ...core.security import get_current_user, CurrentUser
from ...core.tenancy import get_current_tenant_id
from ...services.vanna_service import get_vanna_service
from ...models import QueryHistory

router = APIRouter(prefix="/query", tags=["queries"])


class QueryRequest(BaseModel):
    question: str
    execute: bool = False  # Whether to execute the query
    use_cache: bool = True


class QueryResponse(BaseModel):
    query_id: str
    question: str
    sql: str
    executed: bool = False
    results: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


@router.post("/", response_model=QueryResponse)
async def generate_query(
    request: QueryRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate SQL from natural language question
    Optionally execute the query and return results
    """
    from uuid import UUID
    
    tenant_id = current_user.tenant_id
    user_id = current_user.user_id
    
    # Convert tenant_id and user_id to UUID if they're strings
    if isinstance(tenant_id, str):
        tenant_id = UUID(tenant_id)
    if isinstance(user_id, str):
        try:
            user_id = UUID(user_id)
        except (ValueError, AttributeError):
            # If user_id is not a valid UUID (like "dev-admin-001"), set to None
            user_id = None
    
    # Get Vanna service
    vanna = get_vanna_service(str(tenant_id))
    
    try:
        # Generate SQL
        print(f"Generating SQL for question: {request.question}")
        sql = await vanna.generate_sql(request.question, use_cache=request.use_cache)
        print(f"Generated SQL: {sql}")
        
        # Create query history record
        print(f"Creating query history with tenant_id={tenant_id}, user_id={user_id}")
        query_history = QueryHistory(
            tenant_id=tenant_id,
            user_id=user_id,  # Can be None for dev users
            question=request.question,
            generated_sql=sql,
            was_executed=request.execute,
        )
        db.add(query_history)
        print("Flushing to database...")
        await db.flush()
        print(f"Query history created with id: {query_history.query_id}")
        
        response_data = {
            "query_id": str(query_history.query_id),
            "question": request.question,
            "sql": sql,
            "executed": False,
        }
        
        # Execute query if requested
        if request.execute:
            tenant_db = TenantDatabase(str(tenant_id))
            session = await tenant_db.get_session()
            
            try:
                start_time = datetime.now()
                result = await session.execute(text(sql))
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Fetch results
                rows = result.fetchall()
                columns = result.keys()
                
                # Convert to list of dicts
                results = [dict(zip(columns, row)) for row in rows]
                
                # Update query history
                query_history.execution_time_ms = execution_time
                query_history.row_count = len(results)
                
                response_data.update({
                    "executed": True,
                    "results": results,
                    "row_count": len(results),
                    "execution_time_ms": execution_time,
                })
                
            except Exception as e:
                error_msg = str(e)
                query_history.error_message = error_msg
                response_data["error"] = error_msg
                print(f"Error executing SQL: {error_msg}")
                
            finally:
                await session.close()
        
        print("Committing to database...")
        await db.commit()
        print("Success! Returning response")
        
        return QueryResponse(**response_data)
        
    except Exception as e:
        import traceback
        print(f"ERROR in generate_query: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating query: {str(e)}"
        )


class QueryFeedbackRequest(BaseModel):
    rating: Optional[int] = None  # 1-5
    was_helpful: Optional[bool] = None
    feedback: Optional[str] = None


@router.post("/{query_id}/feedback")
async def submit_query_feedback(
    query_id: str,
    feedback: QueryFeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit feedback for a generated query
    """
    # Find query
    from sqlalchemy import select, update
    from uuid import UUID
    
    result = await db.execute(
        select(QueryHistory).where(QueryHistory.query_id == UUID(query_id))
    )
    query = result.scalar_one_or_none()
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    # Verify user has access to this query
    if str(query.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update feedback
    if feedback.rating is not None:
        query.user_rating = feedback.rating
    if feedback.was_helpful is not None:
        query.was_helpful = feedback.was_helpful
    if feedback.feedback is not None:
        query.user_feedback = feedback.feedback
    
    await db.commit()
    
    return {"message": "Feedback submitted"}


@router.get("/history", response_model=List[QueryResponse])
async def get_query_history(
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get query history for current tenant
    """
    from sqlalchemy import select, desc
    from uuid import UUID
    
    tenant_id = current_user.tenant_id if isinstance(current_user.tenant_id, UUID) else UUID(current_user.tenant_id)
    
    result = await db.execute(
        select(QueryHistory)
        .where(QueryHistory.tenant_id == tenant_id)
        .order_by(desc(QueryHistory.created_at))
        .limit(limit)
    )
    
    queries = result.scalars().all()
    
    return [
        QueryResponse(
            query_id=str(q.query_id),
            question=q.question,
            sql=q.generated_sql,
            executed=q.was_executed,
            row_count=q.row_count,
            execution_time_ms=q.execution_time_ms,
            error=q.error_message,
        )
        for q in queries
    ]

