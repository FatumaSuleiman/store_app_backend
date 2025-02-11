
import sys

import uvicorn
sys.path.append('D:/storeApp')

from fastapi import FastAPI,HTTPException,Depends, Request
from endpoints.category_endpoints import category_router
from models import UserLogin,User
from database import find_user,engine,create_db_and_tables
from starlette.responses import JSONResponse
from fastapi import FastAPI,Depends,status
from fastapi.middleware.cors import CORSMiddleware
from auth import AuthHandler
from sqlmodel import Session ,select # type: ignore
from endpoints.user_endpoints import user_router
from endpoints.product_endpoints import product_router
from endpoints.institution_endpoints import inst_router
from endpoints.store_endpoints import store_router
from endpoints.supplier_endpoints import supp_router
from endpoints.customer_endpoints import customer_router
from endpoints.expense_endpoints import exp_router
from endpoints.order_endpoints import order_router
from endpoints.shoppingcart_endpoints import shop_router
from endpoints.account_endpoints import account_router
from endpoints.payment_enpoint import payment_router
import uvicorn
import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials

app=FastAPI()
app.include_router(category_router)
app.include_router(user_router)
app.include_router(product_router)
app.include_router(inst_router)
app.include_router(store_router)
app.include_router(supp_router)
app.include_router(customer_router)
app.include_router(exp_router)
app.include_router(order_router)
app.include_router(shop_router)
app.include_router(account_router)
app.include_router(payment_router)


origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080"
   
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#@app.get('/')
#async def Home():
# return' hello guys?'
session=Session(bind=engine)

auth_handler=AuthHandler()


    
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    statement = select(User).where(User.email =="admin@gmail.com")
    result = session.exec(statement).first()
    if  result is None:
        hashed_pwd = auth_handler.get_password_hash("admin")
        new_user=User(firstName="Admin",lastName="Admin",email="admin@gmail.com",userName="admin",password=hashed_pwd,is_superuser=True, role="admin")
        session.add(new_user)
        session.commit()

@app.post('/login')
def login(user: UserLogin):
    logging.debug(f"Login attempt for username: {user.username}")
    
    user_found = find_user(user.username)
    if not user_found:
        logging.error(f"Login failed: User not found with username {user.username}")
        return JSONResponse(content="Invalid username and/or password", status_code=status.HTTP_401_UNAUTHORIZED)
    
    logging.debug(f"User found: {user_found.userName}, Password: {user_found.password}")
    
    # Verify password
    verified = auth_handler.verify_password(user.password, user_found.password)
    logging.debug(f"Password verification for {user.username}: {verified}")
    
    if not verified:
        logging.error(f"Login failed: Invalid password for user {user.username}")
        return JSONResponse(content="Invalid username and/or password", status_code=status.HTTP_401_UNAUTHORIZED)
    
    # Issue token if login succeeds
    token = auth_handler.encode_token(user_found.userName)
    logging.info(f"Login successful for user {user.username}, token issued.")
    return {'token': token}



@app.post('/logout')
def logout(auth: HTTPAuthorizationCredentials = Security(auth_handler.security)):
    """
    Logout the user by blacklisting the token.
    """
    token = auth.credentials
    if auth_handler.is_token_blacklisted(token):
        raise HTTPException(status_code=400, detail="Token already blacklisted")

    auth_handler.blacklist_token(token)
    return {"message": "Successfully logged out"}


@app.get('/users/profile/')
def get_user_profile(user=Depends(auth_handler.get_current_user)):
    context={
        "user": user
    }
    return context
from fastapi.staticfiles import StaticFiles
#app.mount("/static", StaticFiles(directory="data/ProductImages"), name="static")
#app.mount("/static", StaticFiles(directory="D:/storeApp/data"), name="static")
app.mount("/static", StaticFiles(directory="data"), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)