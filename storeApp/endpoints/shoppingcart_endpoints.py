from fastapi import APIRouter, Security, security, Depends, Query,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Customer,Product,ShoppingCart,ShoppingCartBase,CartProducts
from fastapi import FastAPI, status
from typing import List
from database import engine
from sqlalchemy import func, and_
from auth import AuthHandler
import json

shop_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session
@shop_router.post('/customers/{customer_id}/shoppings/save', response_model=ShoppingCart, tags=["ShoppingCarts"])
async def create_or_update_shopping_cart(
    customer_id: int,
    shopping: ShoppingCartBase,
    shop_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)
):
    try:
        # Step 1: Validate the customer
        cust_statement = select(Customer).where(Customer.id == customer_id, Customer.deletedStatus == False)
        customer = shop_session.exec(cust_statement).first()

        if customer is None:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")

        # Step 2: Retrieve the existing cart
        cart_statement = select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.deletedStatus == False)
        existing_cart = shop_session.exec(cart_statement).first()

        if existing_cart:
            # Convert existing cart items to dictionary for quick lookup
            cart_items = {item["product_id"]: item for item in existing_cart.items}

            # Iterate over incoming shopping items
            for new_item in shopping.items:
                # Check if product exists
                product_statement = select(Product).where(Product.id == new_item.product_id, Product.deletedStatus == False)
                product = shop_session.exec(product_statement).first()
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product with ID {new_item.product_id} not found")

                # **Only add new product if it's not in the cart**
                if new_item.product_id not in cart_items:
                    cart_items[new_item.product_id] = {
                        "product_id": new_item.product_id,
                        "price": product.sellingPrice,
                        "quantity": new_item.quantity,
                    }

            # Update cart with only new items
            existing_cart.items = list(cart_items.values())

            # Explicitly add changes to session
            shop_session.add(existing_cart)
        
        else:
            # Step 3: Create new cart if none exists
            items_list = []
            for item in shopping.items:
                product_statement = select(Product).where(Product.id == item.product_id, Product.deletedStatus == False)
                product = shop_session.exec(product_statement).first()
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")

                items_list.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": product.sellingPrice,
                })

            new_cart = ShoppingCart(customer_id=customer_id, items=items_list)
            shop_session.add(new_cart)

        # Step 4: Commit and refresh
        shop_session.commit()
        shop_session.refresh(existing_cart or new_cart)

        # Step 5: Return updated or created cart
        return existing_cart or new_cart

    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Log the error traceback
        shop_session.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@shop_router.get('/customers/shoppingcarts',tags=['ShoppingCarts'])         
async def get_shopping_carts( shop_session:Session=Depends(get_session),user=Depends(auth_handler.get_current_user)):
     shop_statement=select(ShoppingCart).where(ShoppingCart.deletedStatus==False)
     shopp=shop_session.exec(shop_statement).all()
     
     if not shopp is None:
          
        return shopp

    
@shop_router.get('/customers/shoppingcarts/{customer_id}/all', tags=['ShoppingCarts'])
async def get_shopping_cart_items(
    customer_id: int,
    shop_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)
):
    shop_statement = select(ShoppingCart).where(
        ShoppingCart.customer_id == customer_id,
        func.json_array_length(ShoppingCart.items) > 0,
        ShoppingCart.deletedStatus == False
    )
    shopp = shop_session.exec(shop_statement).first()  # Fetch single shopping cart

    if not shopp:
        return JSONResponse(
            content={"message": f"ShoppingCart with ID {customer_id} not found or deleted"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    cart_items = []

    try:
        items_list = json.loads(shopp.items) if isinstance(shopp.items, str) else shopp.items  # Fix: Ensure JSON is parsed
    except Exception as e:
        return JSONResponse(
            content={"message": f"Error parsing shopping cart items: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    for item in items_list:  # Fix: Iterate over parsed items correctly
        prod_id = item.get("product_id")  # Fix: Using .get() to avoid KeyErrors
        quantity = item.get("quantity", 1)  # Default quantity to 1 if missing

        if not prod_id:
            continue  # Skip if product_id is missing

        prpd_statement = select(Product).where(Product.id == prod_id, Product.deletedStatus == False)
        result = shop_session.exec(prpd_statement).first()

        if not result:
            continue  # Skip if product doesn't exist
        image=f"http://localhost:8000/static/{result.image}"
        context = {
            "product_id":prod_id,
            "productName": result.name,
            "price": result.sellingPrice *quantity,
            "quantity": quantity, # Fix: Correctly access quantity
            "image":image
        }
        cart_items.append(context)

    return cart_items

from sqlalchemy.orm.attributes import flag_modified

@shop_router.put('/customers/{customer_id}/shoppings/{prod_id}/update', response_model=ShoppingCart, tags=["ShoppingCarts"])
async def update_shopping_cart_quantity(
    customer_id: int,
    prod_id: int,
    shop_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)
):
    try:
         # endpint to increase quantity in a cart
        # ✅ Validate Customer
        customer = shop_session.exec(
            select(Customer).where(Customer.id == customer_id, Customer.deletedStatus == False)
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")

        # ✅ Retrieve Shopping Cart
        existing_cart = shop_session.exec(
            select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.deletedStatus == False)
        ).first()
        if not existing_cart:
            raise HTTPException(status_code=404, detail="Shopping cart not found for this customer")

        # ✅ Convert `items` list into a dictionary for easy lookup
        cart_dict = {item["product_id"]: item for item in existing_cart.items}

        # ✅ Check if product exists in the cart
        if prod_id not in cart_dict:
            raise HTTPException(status_code=404, detail=f"Product {prod_id} not found in cart")

        # ✅ Retrieve Product Details
        product = shop_session.exec(
            select(Product).where(Product.id == prod_id, Product.deletedStatus == False)
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {prod_id} not found")

        # ✅ Update the quantity & price
        cart_dict[prod_id]["quantity"] += 1
        cart_dict[prod_id]["price"] = cart_dict[prod_id]["quantity"] * product.sellingPrice

        print("Before Commit - Updated Cart Items:", list(cart_dict.values()))

        # ✅ Explicitly Mark `items` as Modified
        existing_cart.items = list(cart_dict.values())
        flag_modified(existing_cart, "items")  # ✅ Force SQLAlchemy to track change

        # ✅ Print database state before committing
        cart_before_commit = shop_session.exec(
            select(ShoppingCart).where(ShoppingCart.id == existing_cart.id)
        ).first()
        print("Before Commit - DB Cart Items:", cart_before_commit.items)

        shop_session.commit()
        shop_session.refresh(existing_cart)

        # ✅ Print database state after committing
        cart_after_commit = shop_session.exec(
            select(ShoppingCart).where(ShoppingCart.id == existing_cart.id)
        ).first()
        print("After Commit - DB Cart Items:", cart_after_commit.items)

        return existing_cart

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Log full error traceback
        shop_session.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



@shop_router.put('/customers/{customer_id}/shoppings/{prod_id}/decrease', response_model=ShoppingCart, tags=["ShoppingCarts"])
async def decrease_shopping_cart_quantity(
    customer_id: int,
    prod_id: int,
    shop_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)
):
    try:
        # endpint to decrease quantity in a cart
        # ✅ Validate Customer
        customer = shop_session.exec(
            select(Customer).where(Customer.id == customer_id, Customer.deletedStatus == False)
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")

        # ✅ Retrieve Shopping Cart
        existing_cart = shop_session.exec(
            select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.deletedStatus == False)
        ).first()
        if not existing_cart:
            raise HTTPException(status_code=404, detail="Shopping cart not found for this customer")

        # ✅ Convert `items` list into a dictionary for easy lookup
        cart_dict = {item["product_id"]: item for item in existing_cart.items}

        # ✅ Check if product exists in the cart
        if prod_id not in cart_dict:
            raise HTTPException(status_code=404, detail=f"Product {prod_id} not found in cart")

        # ✅ Retrieve Product Details
        product = shop_session.exec(
            select(Product).where(Product.id == prod_id, Product.deletedStatus == False)
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {prod_id} not found")

        # ✅ Update the quantity & price
        cart_dict[prod_id]["quantity"] -= 1
        cart_dict[prod_id]["price"] = cart_dict[prod_id]["quantity"] * product.sellingPrice

        print("Before Commit - Updated Cart Items:", list(cart_dict.values()))

        # ✅ Explicitly Mark `items` as Modified
        existing_cart.items = list(cart_dict.values())
        flag_modified(existing_cart, "items")  # ✅ Force SQLAlchemy to track change

        # ✅ Print database state before committing
        cart_before_commit = shop_session.exec(
            select(ShoppingCart).where(ShoppingCart.id == existing_cart.id)
        ).first()
        print("Before Commit - DB Cart Items:", cart_before_commit.items)

        shop_session.commit()
        shop_session.refresh(existing_cart)

        # ✅ Print database state after committing
        cart_after_commit = shop_session.exec(
            select(ShoppingCart).where(ShoppingCart.id == existing_cart.id)
        ).first()
        print("After Commit - DB Cart Items:", cart_after_commit.items)

        return existing_cart

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Log full error traceback
        shop_session.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


    
@shop_router.delete('/customers/shoppingcarts/{shop_id}/delete',tags=['ShoppingCarts'])         
async def delete_shopping_cart(shop_id:int,shop_session:Session=Depends(get_session),user=Depends(auth_handler.get_current_user)):
     shop_statement=select(ShoppingCart).where(ShoppingCart.id==shop_id,ShoppingCart.deletedStatus==False)
     shopp=shop_session.exec(shop_statement).first()
     if shopp is None:
        return JSONResponse(
            content=f"ShoppingCart  with ID {shop_id} not found or deleted",
            status_code=status.HTTP_404_NOT_FOUND,
            )
     shopp.deletedStatus=True
     shop_session.add(shopp)
     shop_session.commit()
     return JSONResponse(content=f'ShoppingCart of{shop_id} deleted successfully.',status_code=status.HTTP_404_NOT_FOUND)



from fastapi import Request
@shop_router.delete('/customers/{customer_id}/shoppingcarts/{prod_id}/delete', tags=['ShoppingCarts'])
async def remove_cart_item(
    customer_id: int,
    prod_id: int,
    shop_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user)  # Ensure user is retrieved correctly
):
    print(f"Authenticated User: {user}")  # 🔍 Debugging
    print(f"User ID: {user.id}, Request Customer ID: {customer_id}")  # 🔍 Debugging

    if str(user.referenceId) != str(customer_id):  # Convert to string for comparison safety
        print("❌ User is not authorized to modify this cart!")
        raise HTTPException(status_code=403, detail="You can only modify your own shopping cart")

    print("✅ User is authorized!")

    shopping_cart = shop_session.query(ShoppingCart).filter(
        ShoppingCart.customer_id == customer_id,
        ShoppingCart.deletedStatus == False
    ).first()

    if not shopping_cart:
        raise HTTPException(status_code=404, detail=f"ShoppingCart for customer {customer_id} not found")

    updated_items = [item for item in shopping_cart.items if item.get('product_id') != prod_id]

    if len(updated_items) == len(shopping_cart.items):
        raise HTTPException(status_code=404, detail=f"Product {prod_id} not found in shopping cart")

    shopping_cart.items = updated_items
    flag_modified(shopping_cart, "items")  # Force tracking of change
    shop_session.commit()

    return {"message": f"Product {prod_id} removed from ShoppingCart of customer {customer_id}"}
