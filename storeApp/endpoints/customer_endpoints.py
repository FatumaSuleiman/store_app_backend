from fastapi import APIRouter, Security, security, Depends, Query,BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Customer,CustomerBase,User,ShoppingCart,Product,CartProducts
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler
import os
from typing import List

customer_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session

from fastapi.responses import JSONResponse


from fastapi_mail import FastMail, MessageSchema, ConnectionConfig



from dotenv import dotenv_values


import logging
# Configure FastAPI-Mail


# Load environment variables
Credent = dotenv_values(".env")

# Connection configuration
conf = ConnectionConfig(
    MAIL_USERNAME=Credent['MAIL_USERNAME'],
    MAIL_PASSWORD=Credent['MAIL_PASSWORD'],
    MAIL_FROM=Credent['MAIL_FROM'],
    MAIL_PORT=587,  # Port for STARTTLS
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,  # Enable STARTTLS
    MAIL_SSL_TLS=False,  # Disable SSL/TLS
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,  # Default should be True
)

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
class EmailValidator(BaseModel):
    email: EmailStr

@customer_router.post("/customers/save", response_model=Customer, tags=["Customers"])
async def create_customer(
    customer: CustomerBase, 
      background_tasks: BackgroundTasks,
    customer_session: Session = Depends(get_session)
  
):

    """Endpoint to Register a customer"""
    try:
        # Validate email
        try:
            validated_email = EmailValidator(email=customer.email).email
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address provided."
            )
        
        # Check if the customer already exists
        statement = select(User).where(
            User.userName == validated_email, 
            User.deletedStatus == False
        )
        result = customer_session.exec(statement).all()
        
        if len(result) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists. Try another email."
            )

        # Generate a secure random password
        # Manually test password hash and verification
        plain_password = "customer"  # Replace with the password used during registration
        hashed_password = auth_handler.get_password_hash(plain_password)
        logging.debug(f"Generated hash: {hashed_password}")

        is_verified = auth_handler.verify_password(plain_password, hashed_password)
        logging.debug(f"Password verified: {is_verified}")

        print("hashed pasww:",hashed_password)
        
        # Create new customer
        new_customer = Customer(
            firstName=customer.firstName,
            lastName=customer.lastName,
            email=validated_email,
            phone=customer.phone,
            address=customer.address,
            accountNumber=customer.accountNumber,
            cardNumber=customer.cardNumber,
        )
        customer_session.add(new_customer)
        customer_session.commit()
        customer_session.refresh(new_customer)  # Get ID of the new customer
        print("Customer data:", new_customer)



        # Create new user
        new_user = User(
            firstName=customer.firstName,
            lastName=customer.lastName,
            email=validated_email,
            userName=validated_email,
            password=hashed_password,
            is_staff=False,
            is_default_password=True,
            role="customer",
            referenceId=new_customer.id,
            referenceName="Customer"
        )
        customer_session.add(new_user)
        customer_session.commit()
        print("User data:", new_user)

        # Send email with login details
        email_message = MessageSchema(
            subject="Welcome to Online Shopping",
            recipients=[validated_email],
            body=f"""
            Dear {customer.firstName},

            Welcome to Online Shopping! 
            Here are your login details:
            
            Username: {validated_email}
            Password: {plain_password}
            
            Please change your password after logging in for the first time.

            Regards,
            Online Shopping Team
            """,
            subtype="plain"
        )
        fast_mail = FastMail(conf)
        background_tasks.add_task(fast_mail.send_message, email_message)

        return JSONResponse(
        content={"id": new_customer.id, "user_id": new_user.id,"message": "Customer registered successfully!"},
        status_code=status.HTTP_201_CREATED
    )


    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(
            content=f"Error: {str(e)}", 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@customer_router.get('/all/customers',tags=["Customers"])
async def fetch_customers(customer_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Customers """

    try:
        statement = select(Customer).where(Customer.deletedStatus==False)
        result =customer_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Customers  are   Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@customer_router.get('/customers/{customer_id}/',response_model=Customer,tags=["Customers"])
async def fetch_customer_detail(customer_id:int,customer_session: Session = Depends(get_session)):
    """ Endpoint to Return  Customer Detail """

    try:
        statement = select(Customer).where(Customer.id==customer_id,Customer.deletedStatus==False)
        result = customer_session.exec(statement).first()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Customer  with"+str(customer_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@customer_router.put('/customers/{customer_id}/update',response_model=Customer,tags=["Customers"])
async def update_Customer(customer_id:int,customer:CustomerBase,customer_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update customer Data """

    try:
        statement = select(Customer).where(Customer.id==customer_id,Customer.deletedStatus==False)
        result = customer_session.exec(statement).first()

        if not result is None:
            result.firstName=customer.firstName
            result.lastName=customer.lastName
            result.email=customer.email
            result.phone=customer.phone
            result.address=customer.address
            result.accountNumber =customer.accountNumber
            result.cardNumber=customer.cardNumber
            customer_session.add(result)
            customer_session.commit()
            return result
        else:
            return JSONResponse(content="Customer with "+str(customer_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@customer_router.delete('/customers/{customer_id}/delete',response_model=Customer,tags=["Customers"])
async def delete_customer(customer_id:int,customer_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete  customer  """

    try:
        statement = select(Customer).where(Customer.id==customer_id,Customer.deletedStatus==False)
        result = customer_session.exec(statement).first()
        if result is not None:
            result.deletedStatus=True
            customer_session.add(result)
            customer_session.commit()
            return result
        else:
            return JSONResponse(content="Customer with"+str(customer_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@customer_router.get('/customers/{customer_id}/shoppingCarts',response_model=List[CartProducts],tags=["Customers"])
async def fetch_customer_cart_products(customer_id:int,customer_session: Session = Depends(get_session)):
    """ Endpoint to Return  Customer cart Products """

    try:
        statement = select(ShoppingCart).where(ShoppingCart.customer_id==customer_id,ShoppingCart.deletedStatus==False)
        result = customer_session.exec(statement).first()
        customerProds=[]
        if result is not None:
            products=result.items
            for product in products:
                product_id = product['product_id']
                statP = select(Product).where(Product.id==product_id,Product.deletedStatus==False)
                prod=customer_session.exec(statP).first()
                if not prod is None:
                    productName=prod.name
                
                    context={
                        'productName':productName,
                        'quantity':product['quantity'],
                        'price':product['price']
                    }
                    customerProds.append(context)
                else:
                    return JSONResponse(content="Product  with"+str(product_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

            print('*****************************************',customerProds)
            return customerProds
        else:
            return JSONResponse(content="Customer  with"+str(customer_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



