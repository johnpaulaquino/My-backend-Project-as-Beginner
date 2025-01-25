from pydantic import BaseModel
from datetime import date

# This is the base user
class BaseUser(BaseModel):
    email: str
   


# inherit the attributes of base user
class SignUp(BaseUser):
    password: str
    name : str
    age : int
    b_day : date

class Login(BaseUser):
    password : str
#This will be the response output after signing up
class UserInDB(BaseUser):
    id: str
    name: str
    hash_password : str
    age : int
    b_day : date
    is_active: bool
    