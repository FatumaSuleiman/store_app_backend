from fastapi import APIRouter, Security, security, Depends, Query,UploadFile,File
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select,Session
from starlette.responses import JSONResponse
from models import Category,CategoryBase,Product
from fastapi import FastAPI, status
from database import engine
from auth import AuthHandler
import shutil
import os
from fastapi import HTTPException


category_router = APIRouter()
auth_handler=AuthHandler()


def get_session():
    with Session(engine) as session:
        yield session

@category_router.post('/categories/save',response_model=Category,tags=["Categories"])
async def create_category(category:CategoryBase,catetegory_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Create categories""" 

    try:
       
            new_category =Category(name=category.name,description=category.description)
            catetegory_session.add(new_category)
            catetegory_session.commit()
            return new_category
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
from fastapi.encoders import jsonable_encoder


@category_router.get('/categories', tags=["Categories"])
async def fetch_categories(category_session: Session = Depends(get_session),):
    """Endpoint to Return categories"""
    try:
        statement = select(Category).where(Category.deletedStatus == False)
        result = category_session.exec(statement).all()

        # Update image paths
        for category in result:
            if category.image:
                category.image = f"http://localhost:8000/static/{category.image}"

        return jsonable_encoder([category.dict() for category in result])
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content=f"Error: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@category_router.get('/categories/{categ_id}/',response_model=Category,tags=["Categories"])
async def fetch_category_detail(categ_id:int,category_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return  Category Detail """

    try:
        statement = select(Category).where(Category.id==categ_id,Category.deletedStatus==False)
        result = category_session.exec(statement).first()
        if result is not None:
            return result
        else:
            return JSONResponse(content="Category with"+str(categ_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@category_router.put('/categories/{categ_id}/update',response_model=Category,tags=["Categories"])
async def update_category(categ_id:int,category:CategoryBase,category_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Update Category Data """

    try:
        statement = select(Category).where(Category.id==categ_id,Category.deletedStatus==False)
        result = category_session.exec(statement).first()

        if not result is None:
            result.name=category.name
            result.description=category.deascription
            category_session.add(result)
            category_session.commit()
            return result
        else:
            return JSONResponse(content="Category with "+str(categ_id)+" Not Found",status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@category_router.delete('/categories/{categ_id}/delete',response_model=Category,tags=["Categories"])
async def delete_category(categ_id:int,category_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to delete  Category  """

    try:
        statement = select(Category).where(Category.id==categ_id,Category.deletedStatus==False)
        result = category_session.exec(statement).first()
        if result is not None:
            result.deletedStatus=True
            category_session.add(result)
            category_session.commit()
            return result
        else:
            return JSONResponse(content="Category with"+str(categ_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@category_router.put(
    "/categories/{categ_id}/upload_image/", response_model=Category, tags=["Categories"]
)
async def upload_category_image(
    categ_id: int,
    file: UploadFile = File(...),
    categ_session: Session = Depends(get_session),
    user=Depends(auth_handler.get_current_user),
):
    """
    Endpoint to upload and update category image.
    """
    try:
        # Query for the category
        category = categ_session.query(Category).filter_by(
            id=categ_id, deletedStatus=False
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {categ_id} not found",
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
        images_dir = os.path.join(base_dir, "CategoryImages")
        os.makedirs(images_dir, exist_ok=True)

        file_path = os.path.join(
            images_dir, f"{category.uuid}_{file.filename}"
        )

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update the category's image field with relative path
        category.image = f"CategoryImages/{category.uuid}_{file.filename}"
        categ_session.add(category)
        categ_session.commit()
        categ_session.refresh(category)

        return {
            "message": "Image uploaded successfully",
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "image": f"http://localhost:8000/media/{category.image}",
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

@category_router.get('/categories/{categ_id}/products',tags=["Categories"])
async def fetch_category_products(categ_id:int,category_session: Session = Depends(get_session),user=Depends(auth_handler.get_current_user)):
    """ Endpoint to Return  Category Products """

    try:
        statement = select(Product).where(Product.category_id==categ_id,Product.deletedStatus==False)
        result = category_session.exec(statement).all()
        for product in result:
            if product.image:
                product.image = f"http://localhost:8000/static/{product.image}"

                return jsonable_encoder([product.dict() for product in result])
            else:
                return JSONResponse(content="Category with"+str(categ_id)+"Not Found",status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JSONResponse(content="Error:"+str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)