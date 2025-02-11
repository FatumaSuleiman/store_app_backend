from fastapi import APIRouter, Security, security, Depends, Query,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session # type: ignore
from starlette.responses import JSONResponse
from models import Store,StoreBase,Institution,Product,Supplier,StoreProductLink,ProductBase,StoreProductBase,StoreProducts,Expense
from fastapi import FastAPI, status
from typing import List
from database import engine
from auth import AuthHandler

store_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session
  

@store_router.post('/institutions/{inst_id}/stores/save',response_model=Store,tags=["Stores"])
async def create_institution_store(inst_id:int,store:StoreBase,store_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Create Store""" 
    try:
          inst_statement = select(Institution).where(Institution.id == inst_id,Institution.deletedStatus==False)
          institution = store_session.exec(inst_statement).first()
          if not institution is None:
             
               new_store =Store(name=store.name,location=store.location,institution_id =inst_id)
               store_session.add(new_store)
               store_session.commit()
               return new_store
          else:
                return JSONResponse(
                content="Institution with " + str(inst_id) + " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
          print(e)
          return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
         

@store_router.get('/institutions/stores',tags=["Stores"])
async def fetch_institution_stores(store_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Stores """

    try:
        statement = select(Store).where(Store.deletedStatus==False)
        store =store_session.exec(statement).all()
        if  store is not None:
            return store
        else:
            return JSONResponse(content="stores are   Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@store_router.get('/institutions/stores/{store_id}/',response_model=Store,tags=["Stores"])
async def fetch_store_details(store_id:int,store_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return  store Details """

    try:
        statement = select(Store).where(Store.id==store_id,Store.deletedStatus==False)
        result = store_session.exec(statement).first()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Store with"+str(store_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@store_router.put('/institutions/stores/{store_id}/update',response_model=Store,tags=["Stores"])
async def update_store(store_id:int,store:StoreBase,store_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update  Store Data """

    try:
        statement = select(Store).where(Store.id==store_id,Store.deletedStatus==False)
        result = store_session.exec(statement).first()

        if not result is None:
            result.name=store.name
            result.location=store.location
            store_session.add(result)
            store_session.commit()
            return result
        else:
            return JSONResponse(content="Store with "+str(store_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@store_router.delete('/institutions/stores/{store_id}/delete',response_model=Store,tags=["Stores"])
async def delete_store(store_id:int,store_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete  Store """

    try:
        statement = select(Store).where(Store.id==store_id,Store.deletedStatus==False)
        result = store_session.exec(statement).first()
        if result is not None:
            result.deletedStatus=True
            store_session.add(result)
            store_session.commit()
            return result
        else:
            return JSONResponse(content="Category with"+str(store_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@store_router.put('/stores/{store_id}/products/{prod_id}/save', tags=["Stores"])
async def create_store_products(
    st: StoreProductBase,   
    store_session: Session = Depends(get_session), 
    user=Depends(auth_handler.get_current_user)
):
    """ Endpoint to save products to store """
    try:
        # Fetch the supplier for the store
        sup_statement = select(Supplier).where(Supplier.store_id == st.store_id, Supplier.deletedStatus == False)
        supplier = store_session.exec(sup_statement).first()

        if supplier is None:
            return JSONResponse(
                content=f"No Supplier found for store with ID {st.store_id} or they are all deleted",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Checking  if the product is supplied by the supplier
        product_found = False
        for product in supplier.suppliedProducts:
            if product["product_id"] == st.product_id:
                product_found = True
                break

        if product_found:
            # Checking  if the product is already linked to the store
            store_product_link = store_session.exec(
                select(StoreProductLink).where(
                    StoreProductLink.store_id == st.store_id,
                    StoreProductLink.product_id == st.product_id
                )
            ).first()

            if store_product_link:
                # Updating the existing product quantity
                store_product_link.quantity += st.quantity
            else:
                # Create a new store-product link with the specified quantity
                store_product_link = StoreProductLink(
                    product_id=st.product_id, 
                    store_id=st.store_id, 
                    quantity=st.quantity
                )
                print(f"Received store_id: {st.store_id}, product_id: {st.product_id}, quantity: {st.quantity}")
                store_session.add(store_product_link)
            
            store_session.commit()
            store_session.refresh(store_product_link)
            return store_product_link
         
        else:
            return JSONResponse(
                content=f'Product with ID {st.product_id} is not supplied by the supplier of store with ID {st.store_id}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@store_router.get("/stores/{store_id}/products", response_model=List[StoreProducts], tags=["Stores"])
async def get_store_products(store_id: int, store_session: Session = Depends(get_session)):
    """Endpoint to fetch all products for a specific store, including their quantities in stock"""
    try:
        # Query to get all StoreProductLink entries for the store
        statement = select(StoreProductLink).where(StoreProductLink.store_id == store_id)
        store_links = store_session.exec(statement).all()  # Fetch all links

        # Check if the store has any products
        if not store_links:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store with id {store_id} not found or has no products")

        # Fetch the products corresponding to the product IDs in StoreProductLink
        product_ids = [link.product_id for link in store_links]
        statementp = select(Product).where(Product.id.in_(product_ids), Product.deletedStatus == False)
        products = store_session.exec(statementp).all()  # Fetch all products

        # Checking  if there are any products available
        if not products:
            return JSONResponse(
                content=f"No products found for store with ID {store_id} or they are all deleted",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Map the product ID to its quantity in StoreProductLink for quick lookup
        product_quantity_map = {link.product_id: link.quantity for link in store_links}

        #  list of products with quantities
        products_with_quantity = [
            StoreProducts(
                id=product.id,
                name=product.name,
                buyingPrice=product.buyingPrice,
                sellingPrice=product.sellingPrice,
                description=product.description,
                image= f"http://localhost:8000/static/{product.image}",
                quantity=product_quantity_map.get(product.id, 0)
            )
            for product in products
        ]
        return products_with_quantity  # Return the list of products with quantities
       

    except Exception as e:
        print(e)  # Print the error for debugging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")

@store_router.get('/stores/{store_id}/expenses',tags=["Stores"])
async def fetch_store_expenses(store_id:int,store_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return  store expenses """

    try:
        statement = select(Expense).where(Expense.store_id==store_id,Expense.deleteStatus==False)
        result = store_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Expense with"+str(store_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@store_router.get('/stores/{store_id}/suppliers',tags=["Stores"])
async def fetch_store_suppliers(store_id:int,store_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return  store Suppliers """

    try:
        statement = select(Supplier).where(Supplier.store_id==store_id,Supplier.deletedStatus==False)
        result = store_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Supplier with"+str(store_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@store_router.delete("/stores/{store_id}/products/delete/", tags=["Stores"])
async def delete_store_products(store_id: int, store_session: Session = Depends(get_session)):
    """
    Endpoint to delete all products of a store.
    """
    try:
        # Fetch all StoreProductLink entries for the given store
        statement = select(StoreProductLink).where(StoreProductLink.store_id == store_id)
        store_links = store_session.exec(statement).all()

        # If no links found, raise an exception
        if not store_links:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with ID {store_id} not found or has no associated products"
            )

        # Collect all product IDs associated with the store
        product_ids = [link.product_id for link in store_links]

        # Fetch products that are not marked as deleted
        statementp = select(Product).where(Product.id.in_(product_ids), Product.deletedStatus == False)
        products = store_session.exec(statementp).all()

        # If no products are found
        if not products:
            return JSONResponse(
                content={"message": f"No active products found for store with ID {store_id}"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Delete StoreProductLink entries
        for link in store_links:
            store_session.delete(link)


        # Commit the changes to the database
        store_session.commit()

        return JSONResponse(
            content={"message": f"All products for store with ID {store_id} deleted successfully"},
            status_code=status.HTTP_200_OK,
        )

    except HTTPException as http_err:
        raise http_err  # Re-raise HTTP exceptions for proper status handling
    except Exception as e:
        print(f"Error deleting products for store {store_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting products"
        )
