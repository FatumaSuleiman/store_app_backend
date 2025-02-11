from fastapi import APIRouter, Security, security, Depends, Query,UploadFile,File
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Product,Category,ProductBase,Supplier
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler
import os,shutil
from fastapi import HTTPException

product_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session




@product_router.post(
    "/categories/{categ_id}/products/save",
    response_model=Product,
    tags=["Products"],
)
async def create_product(categ_id: int,prod:ProductBase,prod_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user),
):
    """Endpoint to Create  product"""

    try:
        statement = select(Category).where(
            Category.id == categ_id, Category.deletedStatus == False
        )
        categ = prod_session.exec(statement).first()
        if not categ is None :
          
            new_prod = Product(name=prod.name,buyingPrice=prod.buyingPrice,sellingPrice=prod.sellingPrice,quantity=prod.quantity,description=prod.description,category_id =categ_id)
            prod_session.add(new_prod)
            prod_session.commit()

            
            return new_prod
        else:
            return JSONResponse(
                content="Category  with " + str(categ_id )+ " Not Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        print(e)
        return JSONResponse(
            content="Error: " + str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
 
@product_router.get('/products',tags=["Products"])
async def fetch_categ_products(prod_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Products """

    try:
        statement = select(Product).where(Product.deletedStatus==False)
        result =prod_session.exec(statement).all()
        if result is not None:
            for product in result:
                 if product.image:
                    product.image = f"http://localhost:8000/static/{product.image}"
            
            return jsonable_encoder([product.dict() for product in result])
        else:
            return JSONResponse(content="Products are   Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@product_router.get('/categories/products/{prod_id}/',response_model=Product,tags=["Products"])
async def fetch_product_detail(prod_id:int,prod_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return Product Detail """

    try:
        statement = select(Product).where(Product.id==prod_id,Product.deletedStatus==False)
        result = prod_session.exec(statement).first()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Product with"+str(prod_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@product_router.put('/categories/products/{prod_id}/update',response_model=Product,tags=["Products"])
async def update_product(prod_id:int,product:ProductBase,prod_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update product Data """

    try:
        statement = select(Product).where(Product.id==prod_id,Product.deletedStatus==False)
        result = prod_session.exec(statement).first()

        if not result is None:
            result.name=product.name
            result.sellingPrice = product.sellingPrice
            result.buyingPrice = product.buyingPrice
            result.quantity=product.quantity
            result.description=product.description
            result.category_id =Category.id
            prod_session.add(result)
            prod_session.commit()
            return result
        else:
            return JSONResponse(content="Product with "+str(prod_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@product_router.delete('/categories/products/{prod_id}/delete',response_model=Product,tags=["Products"])
async def delete_product_details(prod_id:int,prod_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete Product """

    try:
        statement = select(Product).where(Product.id==prod_id,Product.deletedStatus==False)
        result = prod_session.exec(statement).first()
        if result is not None:
            result.deletedStatus =True
            prod_session.add(result)
            prod_session.commit()
            return result
        else:
            return JSONResponse(content="Product with"+str(prod_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)





@product_router.put(
    "/categories/products/{prod_id}/upload_image/", response_model=Product, tags=["Products"]
)
async def upload_product_image(
    prod_id: int,
    file: UploadFile = File(...),
    categ_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user),
):
    """
    Endpoint to upload and update product image.
    """
    try:
        # Query for the category
        product = categ_session.query(Product).filter_by(
            id=prod_id, deletedStatus=False
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {prod_id} not found",
            )

        # Validate file type
        allowed_extensions = {"jpg", "jpeg", "png", "gif","jfif"}
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Allowed types: {allowed_extensions}",
            )

        # Define file path
        base_dir = os.environ.get("FILE_SOURCE", "./data")
        images_dir = os.path.join(base_dir, "ProductImages")
        os.makedirs(images_dir, exist_ok=True)

        file_path = os.path.join(
            images_dir, f"{product.uuid}_{file.filename}"
        )

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update the category's image field with relative path
        product.image = f"ProductImages/{product.uuid}_{file.filename}"
        categ_session.add(product)
        categ_session.commit()
        categ_session.refresh(product)

        return {
            "message": "Image uploaded successfully",
            "category": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "quantity":product.quantity,
                "sellingPrice":product.sellingPrice,
                "buyingPrice":product.buyingPrice,
                "image": f"http://localhost:8000/media/{product.image}",
            },
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        print("Error:", str(e))
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )