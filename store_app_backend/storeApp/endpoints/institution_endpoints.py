from fastapi import APIRouter, Security, security, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Institution,InstitutionBase,Store,User
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler
from typing import List

inst_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session

@inst_router.post('/institutions/save',response_model=Institution,tags=["Institutions"])
async def create_institution(institution:InstitutionBase,inst_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Create institution""" 

    try:
       
            new_institution =Institution(name=institution.name,email=institution.email,phone=institution.phone,address=institution.address,invoicing_period_type=institution.invoicing_period_type)
            inst_session.add(new_institution)
            inst_session.commit()
            return new_institution
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@inst_router.get('/all/institutions',tags=["Institutions"])
async def fetch_institutions(inst_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Institutions """

    try:
        statement = select(Institution).where(Institution.deletedStatus==False)
        result =inst_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Institutions  are   Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@inst_router.get('/institutions/{inst_id}/',response_model=Institution,tags=["Institutions"])
async def fetch_institution_detail(inst_id:int,inst_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return  Institution Detail """

    try:
        statement = select(Institution).where(Institution.id==inst_id,Institution.deletedStatus==False)
        result = inst_session.exec(statement).first()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Institution  with"+str(inst_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@inst_router.put('/institutions/{inst_id}/update',response_model=Institution,tags=["Institutions"])
async def update_institution(inst_id:int,institution:InstitutionBase,inst_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update institution Data """

    try:
        statement = select(Institution).where(Institution.id==inst_id,Institution.deletedStatus==False)
        result = inst_session.exec(statement).first()

        if not result is None:
            result.name=institution.name
            result.email=institution.email
            result.phone=institution.phone
            result.address=institution.address
            result.invoicing_period_type=institution.invoicing_period_type
            inst_session.add(result)
            inst_session.commit()
            return result
        else:
            return JSONResponse(content="Institution with "+str(inst_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@inst_router.delete('/institutions/{inst_id}/delete',response_model=Institution,tags=["Institutions"])
async def delete_institution(inst_id:int,inst_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete  institution  """

    try:
        statement = select(Institution).where(Institution.id==inst_id,Institution.deletedStatus==False)
        result = inst_session.exec(statement).first()
        if result is not None:
            result.deletedStatus=True
            inst_session.add(result)
            inst_session.commit()
            return result
        else:
            return JSONResponse(content="Institution with"+str(inst_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@inst_router.get('/institutions/{inst_id}/stores', tags=["Institutions"])
async def fetch_institution_stores(
    inst_id: int, 
    inst_session: Session = Depends(get_session), 
    user=Depends(auth_handler.get_current_user)
):
    """Endpoint to Return Institution stores"""
    try:
        statement = select(Store).where(Store.institution_id == inst_id, Store.deletedStatus == False)
        result = inst_session.exec(statement).all()
        if result:
            return result
        else:
            return JSONResponse(content=f"Institution with ID {inst_id} Not Found", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content=f"Error: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@inst_router.get('/institutions/{inst_id}/users', tags=["Institutions"])
async def fetch_institution_users(
    inst_id: int, 
    inst_session: Session = Depends(get_session), 
    user=Depends(auth_handler.get_current_user)
):
    """Endpoint to Return Institution users"""
    try:
        statement = select(User).where(User.referenceId == str(inst_id),User.referenceName =='Institution',User.deletedStatus == False)
        result = inst_session.exec(statement).all()
        if result:
            print("*****************************",result)    
            return result
      
           
        else:
            return JSONResponse(content=f"Institution with ID {inst_id} Not Found", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content=f"Error: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

