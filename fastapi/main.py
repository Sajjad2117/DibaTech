import json
from datetime import timedelta, datetime
from fastapi import FastAPI, Query, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ValidationError, validator
from models import Product, User
from mongoengine import connect
from mongoengine.queryset.visitor import Q
from passlib.context import CryptContext
from jose import jwt
from fastapi_pagination import Page, add_pagination, paginate, LimitOffsetPage
import schemas

app = FastAPI()
connect(db="dibatech", host="localhost", port=27017)


@app.get("/")
def home():
    return {"message": "Welcome to DibaTech"}


@app.get("/get_all_products", response_model=Page[schemas.Product])
@app.get("/get_all_products/limit-offset", response_model=LimitOffsetPage[schemas.Product])
def get_all_products():
    products = json.loads(Product.objects().to_json())
    return paginate(products)


@app.get("/find_products")
def find_products(name: str, number: int = Query(None)):
    products = json.loads(Product.objects.filter(Q(name__icontains=name) | Q(number=number)).to_json())
    return {"products": products}


class NewProduct(BaseModel):
    name: str
    description: str
    number: int


@app.post("/add_product")
def add_product(product: NewProduct):
    new_product = Product(name=product.name,
                          description=product.description,
                          number=product.number,
                          )
    new_product.save()
    return {"message": "Product added successfully"}


class NewUser(BaseModel):
    username: str
    password: str

    @validator('password')
    def password_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


@app.post("/sign-up")
def sign_up(new_user: NewUser):
    user = User(username=new_user.username,
                password=get_password_hash(new_user.password),
                )
    user.save()
    return {"message": "New user created successfully"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def authenticate_user(username, password):
    try:
        user = json.loads(User.objects.get(username=username).to_json())
        password_check = pwd_context.verify(password, user["password"])
        return password_check
    except User.DoesNotExist:
        return False


SECRET_KEY = "myjwtsecret"
ALGORITHM = 'HS256'


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    if authenticate_user(username, password):
        access_token = create_access_token(data={"sub": username}, expires_delta=timedelta(minutes=15))
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")


class Profile(BaseModel):
    username: str
    first_name: str
    last_name: str
    national_code: int

    @validator("national_code")
    def national_code_must_valid(cls, value):
        if len(str(value)) != 10:
            raise ValueError("Sorry: A valid national_code is required")
        return value


@app.post("/profile/")
def create_profile(new_profile: Profile):
    return new_profile


@app.put("/edit-profile/{profile_id}")
async def edit_profile(profile_id: int, profile: Profile = Body(..., embed=True)):
    results = {
        "profile_id": profile_id,
        "profile": profile
    }
    return results


add_pagination(app)
