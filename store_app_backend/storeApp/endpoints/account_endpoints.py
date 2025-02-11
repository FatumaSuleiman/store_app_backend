from fastapi import APIRouter, Security, security, Depends, Query,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Institution,Account,AccountBase
from fastapi import FastAPI, status
from typing import List
from database import engine
from auth import AuthHandler

account_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session
  

@account_router.post('/institutions/{inst_id}/accounts/save',response_model=Account,tags=["Accounts"])
async def create_institution_account(inst_id:int,account:AccountBase,account_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to save Account""" 
    try:
          inst_statement = select(Institution).where(Institution.id == inst_id,Institution.deletedStatus==False)
          institution = account_session.exec(inst_statement).first()
          if not institution is None:
             
               new_account =Account(account_number=account.account_number, account_name=account.account_name,institution_id =inst_id)
               account_session.add(new_account)
               account_session.commit()
               return new_account
          else:
                return JSONResponse(
                content="Institution with " + str(inst_id) + " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
          print(e)
          return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
@account_router.get('/institutions/accounts',tags=["Accounts"])
async def fetch_accounts(account_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to fetch  Accounts""" 
    try:
          statement = select(Account).where(Account.deletedStatus==False)
          result= account_session.exec(statement).all()
          if not result  is None:
             return result
          else:
                return JSONResponse(
                content="Accounts  are  Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
          print(e)
          return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@account_router.get('/accounts/{account_id}/details',tags=["Accounts"])
async def fetch_account_details(account_id:int,account_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to fetch  Account details """ 
    try:
          statement = select(Account).where( Account.id==account_id,Account.deletedStatus==False)
          result= account_session.exec(statement).first()
          if not result  is None:
             return result
          else:
                return JSONResponse(
                content="Account with "+ str(account_id)+ " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
          print(e)
          return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@account_router.put('/accounts/{account_id}/update',tags=["Accounts"])
async def update_account(account_id:int,account:AccountBase,account_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to update  Account""" 
    try:
          statement = select(Account).where( Account.id==account_id,Account.deletedStatus==False)
          result= account_session.exec(statement).first()
          if not result is None:
             result.account_number=account.account_number
             result.account_name=account.account_name
             account_session.add(result)
             account_session.commit()
             return result
          else:
                return JSONResponse(
                content="Account with "+ str(account_id)+ " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
          print(e)
          return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@account_router.delete('/accounts/{account_id}/delete',tags=["Accounts"])
async def delete_account_details(account_id:int,account_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete  Account details""" 
    try:
          statement = select(Account).where( Account.id==account_id,Account.deletedStatus==False)
          result= account_session.exec(statement).first()
          if not result  is None:
             result.deleteStatus=True
             account_session.add(result)
             account_session.commmit()
             return result
          else:
                return JSONResponse(
                content="Account with "+ str(account_id)+ " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
          print(e)
          return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)