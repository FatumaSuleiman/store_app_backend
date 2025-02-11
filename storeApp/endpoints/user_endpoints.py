from fastapi import APIRouter, Security, security, Depends, Query
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import User,UserBase,NewUserBase,Institution,ChangePasswordBase,StaffUserBase
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler
user_router=APIRouter()
def get_session():
    with Session(engine) as session:
        yield session
auth_handler=AuthHandler()

@user_router.post('/users/save', response_model=User,tags=["Users"])
async def save_user(user:StaffUserBase,user_session: Session = Depends(get_session),user1=Depends(auth_handler.get_current_user)):
    
    try:
        statement = select(User).where(User.userName==user.email,User.deletedStatus==False)
        result = user_session.exec(statement).all()
        print('length')
        print(len(result))
        if len(result)>0:
             return JSONResponse(content="User with such email already exists. Try another email",status_code=status.HTTP_400_BAD_REQUEST)
        else:
            hashed_pwd = auth_handler.get_password_hash("123456")
            new_user=User(firstName=user.firstName,lastName=user.lastName,email=user.email,userName=user.email,password=hashed_pwd,is_default_password=True,is_staff=True,role=user.role)
            user_session.add(new_user)
            user_session.commit()
            return new_user
    except Exception as e:
        return JSONResponse(content="Data Not Found",status_code=status.HTTP_400_BAD_REQUEST)

@user_router.put('/users/{user_id}/update',response_model=User,tags=["Users"])
async def update_user(user_id:int,user1:StaffUserBase,user_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update user Data """

    try:
        statement = select(User).where(User.id==user_id,User.deletedStatus==False)
        result = user_session.exec(statement).first()

        if not result is None:
            hashed_pasw=auth_handler.get_password_hash("123456")
            result.firstName=user1.firstName
            result.lastName=user1.lastName
            result.email=user1.email
            result.userName=user1.email
            result.password=hashed_pasw
            user_session.add(result)
            user_session.commit()
            return result
        else:
            return JSONResponse(content="User with "+str(user_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@user_router.get('/users',tags=["Users"])
async def fetch_users(user_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Users """

    try:
        statement = select(User).where(User.deletedStatus==False)
        result =user_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="users are   Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@user_router.post('/institutions/{institution_id}/users/save', response_model=User,tags=["Users"])
async def save_institution_user(institution_id:int,user:NewUserBase,user_session: Session = Depends(get_session),user1=Depends(auth_handler.get_current_user)):
    """ Endpoint to create user of an institution"""
    statement = select(Institution).where(Institution.id==institution_id)
    result = user_session.exec(statement).first()
    if not result is None:
        hashed_pwd = auth_handler.get_password_hash("123456")
        new_user=User(firstName=user.firstName,lastName=user.lastName,email=user.email,userName=user.email,password=hashed_pwd,is_default_password=True,referenceId=institution_id,referenceName='Institution',role=user.role)
        user_session.add(new_user)
        user_session.commit()

        return new_user
    else:
        return JSONResponse(content="Data Not Found",status_code=status.HTTP_400_BAD_REQUEST)
    
@user_router.post('/users/{user_id}/disable/', response_model=User,tags=["Users"])
async def disable_user(user_id:int,user_session: Session = Depends(get_session)):
    statement = select(User).where(User.id==user_id)
    result = user_session.exec(statement).first()
    if not result is None:
        result.is_active = not result.is_active
        user_session.add(result)
        user_session.commit()
        
        return result
    else:
        return JSONResponse(content="Data Not Found",status_code=status.HTTP_400_BAD_REQUEST)

@user_router.put('/users/{user_id}/change_password/', response_model=User,tags=["Users"])
async def change_user_password(user_id:int,data:ChangePasswordBase,user_session: Session = Depends(get_session)):
    statement = select(User).where(User.id==user_id)
    result = user_session.exec(statement).first()
    if not result is None:
        if data.password == data.confirm_password:
            hashed_pwd = auth_handler.get_password_hash(data.password)
            result.password=hashed_pwd
            result.is_default_password=False
            user_session.add(result)
            user_session.commit()
            
            return result
        else:
             return JSONResponse(content="Password Does Not Match",status_code=status.HTTP_400_BAD_REQUEST)
    else:
        return JSONResponse(content="Data Not Found",status_code=status.HTTP_400_BAD_REQUEST)

@user_router.delete('/users/{user_id}/delete/', response_model=User,tags=["Users"])
async def delete_user(user_id:int,user_session: Session = Depends(get_session)):
    statement = select(User).where(User.id==user_id,User.deletedStatus==False)
    result = user_session.exec(statement).first()
    if not result is None:
            result.deletedStatus=True
            user_session.add(result)
            user_session.commit()
            return result
    else:
        return JSONResponse(content="Data Not Found",status_code=status.HTTP_400_BAD_REQUEST)


@user_router.get('/users/{user_id}/details/', response_model=User,tags=["Users"])
async def get_user(user_id:int,user_session: Session = Depends(get_session)):
    """Endpoint  that fetch user details"""
    statement = select(User).where(User.id==user_id,User.deletedStatus==False)
    result = user_session.exec(statement).first()
    if not result is None:
            return result
    else:
        return JSONResponse(content="Data Not Found",status_code=status.HTTP_400_BAD_REQUEST)






