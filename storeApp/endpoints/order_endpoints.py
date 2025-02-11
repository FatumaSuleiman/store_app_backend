from fastapi import APIRouter, Security, security, Depends,HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Store,Customer,Order,OrderBase,ShoppingCart,Product,StoreProductLink
from fastapi import FastAPI, status
from database import engine
from typing import List
from sqlalchemy import func, and_
from auth import AuthHandler

order_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session

@order_router.post('/orders/{customer_id}/save', response_model=List[Order], tags=["Orders"])  # Return multiple orders
async def create_orders(
    customer_id: int,
    order: OrderBase, 
    order_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)
):
    """ Endpoint to Create Orders for a Customer with Items from Different Stores """ 
    try:
        # Fetch the customer
        statement_customer = select(Customer).where(Customer.id == customer_id, Customer.deletedStatus == False)
        customer = order_session.exec(statement_customer).first()

        if customer is None:
            return JSONResponse(
                content=f"Customer with ID {customer_id} Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Fetch the shopping cart for the customer
        statement_shopping = select(ShoppingCart).where(
                and_(
                    ShoppingCart.customer_id == customer_id,
                    func.json_array_length(ShoppingCart.items) > 0,  # PostgreSQL or MySQL
                    ShoppingCart.deletedStatus == False
                )
            )
        shop_cart = order_session.exec(statement_shopping).first()
        if shop_cart is None:
            return JSONResponse(
                content=f"Customer with ID {customer_id} has no active shopping cart",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Group the items by store using StoreProductLink
        if shop_cart.items !=[]:
        
            store_items = {}  # Dictionary to hold store-specific items
            for cart_item in shop_cart.items:
                prod_id = cart_item["product_id"]

                # Fetch the StoreProductLink for the product
                statement_store_product = select(StoreProductLink).where(StoreProductLink.product_id == prod_id)
                store_link = order_session.exec(statement_store_product).first()

                if store_link is None:
                    print(f"StoreProductLink not found for product ID {prod_id}")
                    return JSONResponse(
                        content=f"Product with ID {prod_id} does not belong to any store",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                store_id = store_link.store_id  # Get the store ID where the product belongs

                # Fetch the product details
                statement_product = select(Product).where(Product.id == prod_id, Product.deletedStatus == False)
                product = order_session.exec(statement_product).first()

                if product is None:
                    return JSONResponse(
                        content=f"Product with ID {prod_id} not found or deleted",
                        status_code=status.HTTP_404_NOT_FOUND,
                    )

                # Add product to the correct store group
                if store_id not in store_items:
                    store_items[store_id] = []  # Initialize the store's item list if not present
                   
                    store_items[store_id].append({
                    "product_id": prod_id,
                    "price": product.sellingPrice,
                    "quantity": cart_item["quantity"]
                })
                     
            # Now create orders for each store

            orders_list = []

            for store_id, items in store_items.items():
                totalAmount = 0 # Initialize total amount for this store
               

                # Calculate total amount for this store's order
                for item in items:
                    if not item["quantity"]>0:
                        return JSONResponse(
                content=f"Product  is not in the stock.",
                
            )

                totalAmount += item["quantity"] * item["price"]

                

            # Create a new order for the store
                new_order = Order(
                    status=order.status,
                    orderDate=order.orderDate,
                    items=items,  # Add the store's items to the order
                    store_id=store_id,  # The store associated with this order
                    customer_id=customer_id,  # The customer placing the order
                    totalAmount=totalAmount # Save the total amount of the order
                )

                order_session.add(new_order)
                orders_list.append(new_order)  # Keep track of the orders

            # Commit all the new orders
            order_session.commit()

            return orders_list  # Return the list of orders (one per store)
        else:
             return JSONResponse(
                        content=f" Items   with Customer  ID {customer_id} not found or deleted",
                        status_code=status.HTTP_404_NOT_FOUND,
                    )

    except Exception as e:
        print(e)
        return JSONResponse(
            content="Error:" + str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

 
@order_router.get('/orders',tags=["Orders"])
async def fetch_customer_order(order_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Oders """

    try:
        statement = select(Order).where(Order.deletedStatus==False)
        result =order_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Orders are   Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@order_router.get('/orders/{order_int}/details',tags=["Orders"])
async def fetch_customer_order(order_id:int,order_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Oder details """

    try:
        statement = select(Order).where(Order.id==order_id,Order.deletedStatus==False)
        result =order_session.exec(statement).first()
        if result is not None:
            return result
        else:
              return JSONResponse(content="order with"+str(order_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@order_router.put('/orders/{order_int}/update',tags=["Orders"])
async def update_customer_order(order_id:int,order:OrderBase,order_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to update Oder details """

    try:
        statement = select(Order).where(Order.id==order_id,Order.deletedStatus==False)
        result =order_session.exec(statement).first()
        
        if result is not None:
          result.orderDate=order.orderDate
          result.status=order.status
          result.totalAmount= order.totalAmount
          order_session.add(result)
          order_session.commit()
        
          return result
        
        else:
              return JSONResponse(content="order with"+str(order_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


