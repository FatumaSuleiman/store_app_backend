from fastapi import APIRouter, Security, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select, Session
from starlette.responses import JSONResponse
from models import Customer, Order, Payment,ShoppingCart,Store,StoreProductLink
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler
import requests
import os
from dotenv import load_dotenv
load_dotenv('.env')
payment_router = APIRouter()
auth_handler = AuthHandler()

def get_session():
    with Session(engine) as session:
        yield session

@payment_router.post('/payments/{customer_id}/orders/bankaccount', tags=['Payments'])
async def order_payment_by_bank_account(
    customer_id: int,
    accountNumber:str,
    payment_method: str,
    payment_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)
):
    """ Endpoint for Payment by Account Number."""
    # 1. Retrieve the Customer
    if not accountNumber or not payment_method:
       return JSONResponse(
         content="accountNumber and payment_method are required",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

    customer_statement = select(Customer).where(Customer.id == customer_id, Customer.deletedStatus == False)
    customer = payment_session.exec(customer_statement).first()
    if customer is None:
        return JSONResponse(
            content=f"Customer with ID {customer_id} not found or deleted",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 2. Retrieve the Order
    order_statement = select(Order).where(Order.customer_id == customer_id, Order.status == 'Pending', Order.deletedStatus == False)
    order = payment_session.exec(order_statement).first()
    if order is None:
        return JSONResponse(
            content=f"Order for Customer ID {customer_id} not found or deleted, or its status is not Pending",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 3. Fetch Bank Customer Details
    response = requests.get(f'http://localhost:8002/bankcustomers/{accountNumber}/details')
    if response.status_code != 200:
        return JSONResponse(content='Bank Customer details not found', status_code=500)

    bank_customer = response.json()

    # 4. Payment Processing
    if payment_method == 'PaymentByAccountNumber':
        if customer.accountNumber != accountNumber:
            return JSONResponse(
                content="Account number does not match",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    elif payment_method == 'PaymentByCardNumber':
        if customer.cardNumber != bank_customer['cardNumber']:
            return JSONResponse(
                content="Card number does not match",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return JSONResponse(
            content="Invalid payment method",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Deduct the order amount from the Bank Customer's balance
    if bank_customer['balance'] < order.totalAmount:
        return JSONResponse(
            content="Insufficient funds",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    new_balance = bank_customer['balance'] - order.totalAmount

    # 5. Update the Bank Customer's Balance
    update_response = requests.put(
        f'http://localhost:8002/bankcustomers/{accountNumber}/update',
        json={
            'firstName': bank_customer['firstName'],
            'lastName': bank_customer['lastName'],
            'accountNumber': bank_customer['accountNumber'],
            'cardNumber': bank_customer['cardNumber'],
            'balance': new_balance,
            'phone': bank_customer['phone']
        }
    )
    if update_response.status_code != 200:
        return JSONResponse(
            content="Failed to update the bank customer's balance",
            status_code=500
        )

    # 6. Create a Transaction Record
    account_to_credit = os.getenv('ACCOUNT_TO_CREDIT')
    if account_to_credit is None:
        raise ValueError("The ACCOUNT_TO_CREDIT environment variable is not set.")
    transaction_data = {
        'accountNumber': customer.accountNumber,
        'cardNumber': customer.cardNumber,
        'balance': new_balance,
        'phone': customer.phone,
        'account_to_debit': customer.accountNumber,
        'account_to_credit': account_to_credit,
        'paymentStatus': "Completed",
        'transactionDate':order.orderDate,
        'paymentDescription': f"Payment for order {order.id}",
        'bankcustomer_id': bank_customer['id']
    }

    transaction_response = requests.post(
        f'http://localhost:8002/transactions/{accountNumber}/create',
        json=transaction_data
    )
    if transaction_response.status_code != 200:
        return JSONResponse(
            content="Failed to create the transaction record",
            status_code=500
        )

    # 7. Record Payment in the Local Database
    new_payment = Payment(amount=order.totalAmount, paymentMethod=payment_method, order_id=order.id)
    payment_session.add(new_payment)
    payment_session.commit()

   # 8. Update the Order Status to "Paid" and reduce the quantity of items from the related store
    order.status = 'Paid'
    payment_session.add(order)
    payment_session.commit()

    store_id = order.store_id
    store_statement = select(Store).where(Store.id == store_id, Store.deletedStatus == False)
    store = payment_session.exec(store_statement).first()

    if store is None:
        return JSONResponse(
            content=f"Store with ID {store_id} not found or deleted",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    order_products = order.items
    store_products_updated = False

    for product in order_products:
        # Retrieve the store product link
        store_product_link = payment_session.exec(
            select(StoreProductLink).where(
                StoreProductLink.store_id == store_id,
                StoreProductLink.product_id == product['product_id']
            )
        ).first()

        if store_product_link:
           
           # Ensure the quantity is not None; set a default value if needed
            current_quantity = store_product_link.quantity if store_product_link.quantity is not None else 0

            # Perform the subtraction
            new_quantity = current_quantity - product['quantity']

            # Update the quantity
            store_product_link.quantity = new_quantity

            store_products_updated = True
        else:
            return JSONResponse(
                content=f"Product with ID {product['product_id']} not found in store with ID {store_id}",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if store_products_updated:
            # Commit the changes to the store product link
            payment_session.add(store_product_link)
            payment_session.commit()
        else:
            return JSONResponse(
                content="No matching products found in the store to update quantities",
                status_code=status.HTTP_404_NOT_FOUND,
            )

    # 9. Clear items from the Shopping Cart
    shop_statement = select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.deletedStatus == False)
    shop = payment_session.exec(shop_statement).first()
    if shop:
        shop.items = []  # Clear the items list
        payment_session.add(shop)
        payment_session.commit()

    return JSONResponse(
        content=f"Payment of {order.totalAmount} completed successfully for Order ID {order.id}",
        status_code=status.HTTP_200_OK,
    )


@payment_router.post('/payments/{customer_id}/orders/phone', tags=['Payments'])
async def order_payment_by_phone(
    customer_id: int,
    accountNumber: str,
    payment_method: str,
    payment_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)
):
    """ Endpoint for payment by phone"""
    # 1. Retrieve the Customer
    customer_statement = select(Customer).where(Customer.id == customer_id, Customer.deletedStatus == False)
    customer = payment_session.exec(customer_statement).first()
    if customer is None:
        return JSONResponse(
            content=f"Customer with ID {customer_id} not found or deleted",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 2. Retrieve the Order
    order_statement = select(Order).where(Order.customer_id == customer_id, Order.status == 'Pending', Order.deletedStatus == False)
    order = payment_session.exec(order_statement).first()
    if order is None:
        return JSONResponse(
            content=f"Order for Customer ID {customer_id} not found or deleted, or its status is not Pending",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 3. Fetch Bank Customer Details
    response = requests.get(f'http://localhost:8002/bankcustomers/{accountNumber}/details')
    if response.status_code != 200:
        return JSONResponse(content='Bank Customer details not found', status_code=500)

    bank_customer = response.json()

    # 4. Payment Processing
    if payment_method == 'PaymentByPhone':
        if customer.phone != bank_customer['phone']:
            return JSONResponse(
                content="phone  number does not match",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return JSONResponse(
            content="Invalid payment method",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Deduct the order amount from the Bank Customer's balance
    if bank_customer['balance'] < order.totalAmount:
        return JSONResponse(
            content="Insufficient funds",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    new_balance = bank_customer['balance'] - order.totalAmount

    # 5. Update the Bank Customer's Balance
    update_response = requests.put(
        f'http://localhost:8002/bankcustomers/{accountNumber}/update',
        json={
            'firstName': bank_customer['firstName'],
            'lastName': bank_customer['lastName'],
            'accountNumber': bank_customer['accountNumber'],
            'cardNumber': bank_customer['cardNumber'],
            'balance': new_balance,
            'phone': bank_customer['phone']
        }
    )
    if update_response.status_code != 200:
        return JSONResponse(
            content="Failed to update the bank customer's balance",
            status_code=500
        )

    # 6. Create a Transaction Record
    account_to_credit = os.getenv('ACCOUNT_TO_CREDIT')
    if account_to_credit is None:
        raise ValueError("The ACCOUNT_TO_CREDIT environment variable is not set.")
    transaction_data = {
        'accountNumber': customer.accountNumber,
        'cardNumber': customer.cardNumber,
        'balance': new_balance,
        'phone': customer.phone,
        'account_to_debit': customer.accountNumber,
        'account_to_credit': account_to_credit,
        'paymentStatus': "Completed",
        'paymentDescription': f"Payment for order {order.id}",
        'bankcustomer_id': bank_customer['id']
    }

    transaction_response = requests.post(
        f'http://localhost:8002/transactions/{accountNumber}/create',
        json=transaction_data
    )
    if transaction_response.status_code != 200:
        return JSONResponse(
            content="Failed to create the transaction record",
            status_code=500
        )

    # 7. Record Payment in the Local Database
    new_payment = Payment(amount=order.totalAmount, paymentMethod=payment_method, order_id=order.id)
    payment_session.add(new_payment)
    payment_session.commit()

   # 8. Update the Order Status to "Paid" and reduce the quantity of items from the related store
    order.status = 'Paid'
    payment_session.add(order)
    payment_session.commit()

    store_id = order.store_id
    store_statement = select(Store).where(Store.id == store_id, Store.deletedStatus == False)
    store = payment_session.exec(store_statement).first()

    if store is None:
        return JSONResponse(
            content=f"Store with ID {store_id} not found or deleted",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    order_products = order.items
    store_products_updated = False

    for product in order_products:
        # Retrieve the store product link
        store_product_link = payment_session.exec(
            select(StoreProductLink).where(
                StoreProductLink.store_id == store_id,
                StoreProductLink.product_id == product['product_id']
            )
        ).first()

        if store_product_link:
           
           # Ensure the quantity is not None; set a default value if needed
            current_quantity = store_product_link.quantity if store_product_link.quantity is not None else 0

            # Perform the subtraction
            new_quantity = current_quantity - product['quantity']

            # Update the quantity
            store_product_link.quantity = new_quantity

            store_products_updated = True
        else:
            return JSONResponse(
                content=f"Product with ID {product['product_id']} not found in store with ID {store_id}",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if store_products_updated:
            # Commit the changes to the store product link
            payment_session.add(store_product_link)
            payment_session.commit()
        else:
            return JSONResponse(
                content="No matching products found in the store to update quantities",
                status_code=status.HTTP_404_NOT_FOUND,
            )

    # 9. Clear items from the Shopping Cart
    shop_statement = select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.deletedStatus == False)
    shop = payment_session.exec(shop_statement).first()
    if shop:
        shop.items = []  # Clear the items list
        payment_session.add(shop)
        payment_session.commit()

    return JSONResponse(
        content=f"Payment of {order.totalAmount} completed successfully for Order ID {order.id}",
        status_code=status.HTTP_200_OK,
    )
