from fastapi import APIRouter, Security, security, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Store,Supplier,SupplierBase,SupplierProduct,Product,SupplierProductsB
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler
from typing import List

supp_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session




@supp_router.put(
    "/stores/{sup_id}/suppliers/products/create",
    response_model=Supplier,
    tags=["Suppliers"],
)
async def create_store_supplier_products(sup_id: int,supplier:SupplierProduct,sup_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user),
):
    """Endpoint to Create Store SupplierProducts"""

    try:
        statement = select(Supplier).where(
            Supplier.id == sup_id, Store.deletedStatus == False
        )
        sup =sup_session.exec(statement).first()
        supProducts=[]
        if not sup is None:
            for product in supplier.products:
                prod_id=product.product_id
                qty=product.quantity
                p_statement=select(Product).where(Product.id==prod_id,Product.deletedStatus==False)
                prod=sup_session.exec(p_statement).first()
                if prod is None:
                    return JSONResponse(
                           content=f"Product with ID {prod_id} not found or deleted",
                           status_code=status.HTTP_404_NOT_FOUND,
                       )
                context={
                    "product_id":prod_id,
                    "quantity":qty,
                    "price":prod.buyingPrice
                }
                supProducts.append(context)
            sup.suppliedProducts=supProducts
            sup_session.add(sup)
            sup_session.commit()
            return sup
            
        else:
            return JSONResponse(
                content="Supplier with " + str(sup_id) + " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        print(e)
        return JSONResponse(
            content="Error: " + str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
 
@supp_router.get('/suppliers',tags=["Suppliers"])
async def fetch_store_suppliers(supp_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Suppliers """

    try:
        statement = select(Supplier).where(Supplier.deletedStatus==False)
        result =supp_session.exec(statement).all()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Suppliers are   Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@supp_router.get('/stores/suppliers/{sup_id}/',response_model=Supplier,tags=["Suppliers"])
async def fetch_supplier_detail(sup_id:int,sup_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return supplier Detail """

    try:
        statement = select(Supplier).where(Supplier.id==sup_id,Supplier.deletedStatus==False)
        result = sup_session.exec(statement).first()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Supplier with"+str(sup_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@supp_router.put('/stores/suppliers/{sup_id}/update',response_model=Supplier,tags=["Suppliers"])
async def update_supplier(sup_id:int,supp:SupplierBase,sup_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update Supplier Data """

    try:
        statement = select(Supplier).where(Supplier.id==sup_id,Supplier.deletedStatus==False)
        result = sup_session.exec(statement).first()

        if not result is None:
            result.name=supp.name
            result.contactPhone = supp.contactPhone
            result.email=supp.email
            sup_session.add(result)
            sup_session.commit()
            return result
        else:
            return JSONResponse(content="Supplier with "+str(sup_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@supp_router.delete('/stores/suppliers/{supp_id}/delete',response_model=Supplier,tags=["Suppliers"])
async def delete_supplier_details(supp_id:int,sup_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete Supplier """

    try:
        statement = select(Supplier).where(Supplier.id==supp_id,Supplier.deletedStatus==False)
        result = sup_session.exec(statement).first()
        if result is not None:
            result.deletedStatus =True
            sup_session.add(result)
            sup_session.commit()
            return result
        else:
            return JSONResponse(content="Supplier with"+str(supp_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@supp_router.post(
    "/stores/{store_id}/suppliers/create",
    response_model=Supplier,
    tags=["Suppliers"],
)
async def create_store_supplier(store_id: int,supplier:SupplierBase,sup_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user),
):
    """Endpoint to Create Store Supplier"""

    try:
        statement = select(Store).where(
            Store.id == store_id, Store.deletedStatus == False
        )
        store =sup_session.exec(statement).first()

        if not store is None:
          
            new_supplier = Supplier(name=supplier.name,contactPhone=supplier.contactPhone,email=supplier.email,store_id =store_id)
            sup_session.add(new_supplier)
            sup_session.commit()
            
            return new_supplier
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
    
 
@supp_router.get('/stores/suppliers/{sup_id}/products',tags=["Suppliers"])
async def fetch_supplier_products(sup_id:int,sup_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return supplier products """

    try:
        statement = select(Supplier).where(Supplier.id==sup_id,Supplier.deletedStatus==False)
        result = sup_session.exec(statement).first()
        sup_products=[]
        if result is not None:
            for p in result.suppliedProducts:
                prod_id = p['product_id']
                print('************************************',prod_id)
                statementp=select(Product).where(Product.id==prod_id,Product.deletedStatus==False)
                product=sup_session.exec(statementp).first()

                context={
                    "productName":product.name,
                    "quantity":p['quantity'],
                    "price":p['price']
                }
                sup_products.append(context)
            return sup_products
        else:
            return JSONResponse(content="Supplier with"+str(sup_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

 
@supp_router.get('/stores/suppliers/{sup_id}/products/clear',tags=["Suppliers"])
async def fetch_supplier_products(sup_id:int,sup_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to clear supplier products """

    try:
        statement = select(Supplier).where(Supplier.id==sup_id,Supplier.deletedStatus==False)
        result = sup_session.exec(statement).first()
        if result is not None:
             result.suppliedProducts=[]
             sup_session.add(result)
             sup_session.commit()
             return result
        else:
            return JSONResponse(content="Supplier with"+str(sup_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



