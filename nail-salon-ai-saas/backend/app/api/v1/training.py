"""
API endpoints for AI training management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from ...core.security import get_current_user, CurrentUser
from ...services.vanna_service import get_vanna_service


router = APIRouter(prefix="/training", tags=["training"])


class TrainingResponse(BaseModel):
    """Training operation response"""
    success: bool
    ddl_trained: bool
    questions_trained: int
    documentation_added: int
    errors: list[str]
    already_trained: Optional[bool] = None
    message: Optional[str] = None


class TrainingStatusResponse(BaseModel):
    """Training status response"""
    is_trained: bool
    tenant_id: str


@router.post("/auto-train", response_model=TrainingResponse)
async def auto_train(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Automatically train AI with standard nail salon schema
    
    This trains the AI on:
    - Complete database schema (7 tables)
    - 30+ example question-SQL pairs
    - Business terminology documentation
    
    Only trains if not already trained. Use /retrain to force retraining.
    """
    vanna_service = get_vanna_service(str(current_user.tenant_id))
    
    try:
        results = await vanna_service.auto_train_tenant_schema()
        
        if results.get("already_trained"):
            return TrainingResponse(
                success=True,
                ddl_trained=False,
                questions_trained=0,
                documentation_added=0,
                errors=[],
                already_trained=True,
                message=results.get("message")
            )
        
        return TrainingResponse(
            success=results.get("success", False),
            ddl_trained=results.get("ddl_trained", False),
            questions_trained=results.get("questions_trained", 0),
            documentation_added=results.get("documentation_added", 0),
            errors=results.get("errors", [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        )


@router.post("/retrain", response_model=TrainingResponse)
async def retrain(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Force retrain AI even if already trained
    
    Use this to:
    - Add new training examples
    - Update after schema changes
    - Improve AI accuracy with additional data
    
    Warning: This adds to existing training data (does not replace it)
    """
    vanna_service = get_vanna_service(str(current_user.tenant_id))
    
    # Force retrain by temporarily bypassing is_trained check
    original_is_trained = vanna_service.is_trained
    vanna_service.is_trained = lambda: False
    
    try:
        results = await vanna_service.auto_train_tenant_schema()
        
        return TrainingResponse(
            success=results.get("success", False),
            ddl_trained=results.get("ddl_trained", False),
            questions_trained=results.get("questions_trained", 0),
            documentation_added=results.get("documentation_added", 0),
            errors=results.get("errors", [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retraining failed: {str(e)}"
        )
    finally:
        vanna_service.is_trained = original_is_trained


@router.get("/status", response_model=TrainingStatusResponse)
async def get_training_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Check if AI has been trained for this tenant
    
    Returns:
        Status indicating if training data exists
    """
    vanna_service = get_vanna_service(str(current_user.tenant_id))
    
    return TrainingStatusResponse(
        is_trained=vanna_service.is_trained(),
        tenant_id=str(current_user.tenant_id)
    )


@router.post("/train-custom")
async def train_custom(
    question: Optional[str] = None,
    sql: Optional[str] = None,
    ddl: Optional[str] = None,
    documentation: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Train AI with custom data
    
    Provide one of:
    - question + sql: Train question-SQL pair
    - ddl: Train database schema
    - documentation: Train business documentation
    
    Args:
        question: Natural language question
        sql: Corresponding SQL query
        ddl: DDL statement
        documentation: Documentation text
    """
    vanna_service = get_vanna_service(str(current_user.tenant_id))
    
    try:
        if question and sql:
            await vanna_service.train_question_sql(question, sql)
            return {
                "success": True,
                "message": "Question-SQL pair trained successfully",
                "type": "question_sql"
            }
        elif ddl:
            await vanna_service.train_schema(ddl)
            return {
                "success": True,
                "message": "DDL trained successfully",
                "type": "ddl"
            }
        elif documentation:
            await vanna_service.train_documentation(documentation)
            return {
                "success": True,
                "message": "Documentation trained successfully",
                "type": "documentation"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either (question + sql), ddl, or documentation"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Custom training failed: {str(e)}"
        )

