from fastapi import APIRouter, Security, security, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Store,Expense,ExpenseBase
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler

exp_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session




@exp_router.post(
    "/stores/{store_id}/expenses/create",
    response_model=Expense,
    tags=["Expenses"],
)
async def create_store_expense(store_id: int,expense:ExpenseBase,exp_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user),
):
    """Endpoint to Create Store Expense"""

    try:
        statement = select(Store).where(
            Store.id == store_id, Store.deletedStatus == False
        )
        store =exp_session.exec(statement).first()

        if not store is None:
          
            new_expense = Expense(name=expense.name,descripion=expense.description,amount=expense.amount,store_id =store_id)
            exp_session.add(new_expense)
            exp_session.commit()
            
            return new_expense
        else:
            return JSONResponse(
                content="Store with " + str(store_id) + " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        print(e)
        return JSONResponse(
            content="Error: " + str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
 
@exp_router.get('/expenses',tags=["Expenses"])
async def fetch_store_expenses(exp_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Expenses """

    try:
        statement = select(Expense).where(Expense.deleteStatus==False)
        result =exp_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Expense are   Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exp_router.get('/stores/expenses/{expense_id}/',response_model=Expense,tags=["Expenses"])
async def fetch_expense_detail(expense_id:int,exp_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return expense Detail """

    try:
        statement = select(Expense).where(Expense.id==expense_id,Expense.deleteStatus==False)
        result = exp_session.exec(statement).first()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Expense with"+str(expense_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exp_router.put('/stores/expenses/{expense_id}/update',response_model=Expense,tags=["Expenses"])
async def update_expense(expense_id:int,expense:ExpenseBase,exp_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update Expense Data """

    try:
        statement = select(Expense).where(Expense.id==expense_id,Expense.deleteStatus==False)
        result = exp_session.exec(statement).first()

        if not result is None:
            result.name=expense.name
            result.description=expense.description
            result.amount = expense.amount
            exp_session.add(result)
            exp_session.commit()
            return result
        else:
            return JSONResponse(content="Expense with "+str(expense_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@exp_router.delete('/stores/expenses/{expense_id}/delete',response_model=Expense,tags=["Expenses"])
async def delete_expense_details(expense_id:int,exp_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete Expense """

    try:
        statement = select(Expense).where(Expense.id==expense_id,Expense.deleteStatus==False)
        result = exp_session.exec(statement).first()
        if result is not None:
            result.deleteStatus =True
            exp_session.add(result)
            exp_session.commit()
            return result
        else:
            return JSONResponse(content="expense with"+str(expense_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    





