import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float, Boolean, JSON
from sqlmodel import Field, SQLModel,Relationship
import uuid as pk
from typing import Optional, List
from datetime import datetime


class Institution(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, nullable=False)
    uuid: pk.UUID = Field(default_factory=pk.uuid4, nullable=False)
    active_status: Optional[str] = Field(default=True)
    name: str = Field(nullable=True)
    phone: str = Field(nullable=True)
    email: str = Field(nullable=True)
    address: Optional[str] = Field(nullable=True)
    deletedStatus: bool = Field(default=False)
    invoicing_period_type: str = Field(nullable=False)


class StoreProductLink(SQLModel, table=True):
    store_id: Optional[int] = Field(foreign_key="store.id", primary_key=True)
    product_id: Optional[int] = Field(foreign_key="product.id", primary_key=True)
    quantity:int=Field(nullable=True)


class Store(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    name: str = Field(nullable=True)
    location: str = Field(nullable=True)
    deletedStatus: bool = Field(default=False)
    products:Optional[List[dict]] = Field(default_factory=list, sa_column=Column(JSON))
    institution_id: Optional[int] = Field(default=None, foreign_key='institution.id')

class Product(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    name: str = Field(nullable=True)
    buyingPrice: float = Field(nullable=True) 
    sellingPrice: float = Field(nullable=True)  
    quantity: int = Field(nullable=True)  
    description: str = Field(nullable=True)
    image: str = Field(nullable=True)
    deletedStatus: bool = Field(default=False)
    category_id: Optional[int] = Field(default=None, foreign_key='category.id')
    

class Category(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    name: str = Field(nullable=True)
    description: str = Field(nullable=True)
    image: str = Field(nullable=True)
    deletedStatus: bool = Field(default=False)



class Order(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    totalAmount: float = Field(nullable=True)  # Changed to Float
    items: Optional[List[dict]] = Field(default_factory=list, sa_column=Column(JSON))
    orderDate: datetime = Field(default_factory=sa.func.now)  
    status: str = Field(nullable=False)
    deletedStatus: bool = Field(default=False)
    customer_id: Optional[int] = Field(default=None, foreign_key='customer.id')
    store_id: Optional[int] = Field(default=None, foreign_key='store.id')

class ShoppingCart(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    items: Optional[List[dict]] = Field(default_factory=list, sa_column=Column(JSON))
    deletedStatus: bool = Field(default=False)
    customer_id: Optional[int] = Field(default=None, foreign_key='customer.id')

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    firstName: str = Field(nullable=True)
    lastName: str = Field(nullable=True)
    email: str = Field(nullable=True)
    address: str = Field(nullable=True)
    phone: str = Field(nullable=True)
    accountNumber: str = Field(nullable=True)
    cardNumber: str = Field(nullable=True)
    deletedStatus: bool = Field(default=False)

class Payment(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    amount: float = Field(nullable=True)  # Changed to Float
    paymentDate: datetime = Field(default_factory=sa.func.now)  # Default to now
    paymentMethod: str = Field(nullable=False)
    deletedStatus: bool = Field(default=False)
    order_id: Optional[int] = Field(default=None, foreign_key='order.id')

class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, nullable=False)
    uuid: pk.UUID = Field(default_factory=pk.uuid4, nullable=False)
    firstName: str = Field(default=None, index=True)
    lastName: str = Field(default=None, index=True)
    userName: str = Field(index=True)
    email: str = Field(index=True)
    password: str = Field(index=True)
    deletedStatus: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    is_superuser: bool = Field(default=False)
    is_staff: bool = Field(default=False)
    is_default_password: bool = Field(default=False)
    is_active: bool = Field(default=True)
    referenceId: Optional[str] = Field(nullable=True)
    referenceName: Optional[str] = Field(nullable=True)
    role: Optional[str] = Field(nullable=True)


class Expense(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    name: str = Field(nullable=True)
    description: str = Field(nullable=True)
    amount: float = Field(nullable=True)  # Changed to Float
    date: datetime = Field(default_factory=sa.func.now) 
    deleteStatus: bool = Field(default=False)
    store_id: Optional[int] = Field(default=None, foreign_key='store.id')
  
class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    name: str = Field(nullable=True)
    contactPhone: str = Field(nullable=True)
    email:str = Field(nullable=True)
    deletedStatus: bool = Field(default=False)
    suppliedProducts:Optional[List[dict]] = Field(default_factory=list, sa_column=Column(JSON))
    store_id: Optional[int] = Field(default=None, foreign_key='store.id')

class Account(SQLModel,table=True):
    id: Optional[int] = Field(primary_key=True)
    uuid: pk.UUID = Field(default_factory=pk.uuid4)
    account_number:str= Field(nullable=True)
    account_name:str = Field(nullable=True)
    institution_id: Optional[int] = Field(default=None, foreign_key='institution.id')
    deletedStatus: bool = Field(default=False)




class Config:
    arbitrary_types_allowed = True
    
class CategoryBase(SQLModel):
    name:str
    description:str

class UserBase(SQLModel):
    firstName: str
    lastName: str
    email: str
    password: str
class UserLogin(SQLModel):
    username: str
    password: str

class ProductBase(SQLModel):
    name:str
    buyingPrice:float
    sellingPrice:float
    quantity:int
    description:str

class InstitutionBase(SQLModel):
    name:str
    email:str
    phone:str
    address:str
    invoicing_period_type: str

class StoreBase(SQLModel):
    name:str
    location:str

class SupplierBase(SQLModel):
    name:str
    contactPhone:str
    email:str

class CustomerBase(SQLModel):
    firstName:str
    lastName:str
    email:str
    address:str
    phone:str
    accountNumber:str
    cardNumber:str
class ExpenseBase(SQLModel):
    name:str
    description:str
    amount:float

class Items(SQLModel):
    product_id:int
    price:float
    quantity:int
   


class OrderBase(SQLModel):
    orderDate:datetime
    status:str
    totalAmount:float

class ShoppingCartBase(SQLModel):
    items:List[Items]

class StoreProductBase(SQLModel):
    product_id:int
    store_id:int
    quantity:int

class SupplierProduct(SQLModel):
    products:List[Items]

class NewUserBase(SQLModel):
    firstName: str
    lastName: str
    email: str
    role:str

class ChangePasswordBase(SQLModel):
    password: str
    confirm_password: str

class StaffUserBase(SQLModel):
    firstName: str
    lastName: str
    email: str
    role: str

class StaffUserBase(SQLModel):
    firstName: str
    lastName: str
    email: str
    role: str
class AccountBase(SQLModel):
    account_number:str
    account_name:str


class StoreProducts(SQLModel):
    name:str
    buyingPrice:float
    sellingPrice:float
    quantity:int
    description:str
    image:str
class SupplierProductsB(SQLModel):
    productId:int
    quantity:int
    price:float
class CartProducts(SQLModel):
    productName:str
    quantity:int
    price:float
