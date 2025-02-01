from uuid import uuid4

from argon2.exceptions import Argon2Error
from fastapi_mail import MessageSchema
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone

from taskmanagement.pydantic_models.email_schema import EmailSchema
from taskmanagement.pydantic_models.settings import Settings
from contextlib import asynccontextmanager
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from starlette.responses import JSONResponse
from taskmanagement.pydantic_models.users_schema import TokenData, UserInDB
import pyotp


contex_password = CryptContext(schemes=['argon2'], deprecated='auto')
settings = Settings()
generate_code = pyotp.TOTP(pyotp.random_base32())

class Utility:
    @staticmethod
    def generate_uuid() -> str:
        """
        
        :return:
            The uuid in a string
        """
        return str(uuid4())
    
    @staticmethod
    def generate_access_token(data: dict):
        """
        
        :param data:
            This is the data that will encode to the token
        :return:
            the token
        """
        to_encode = data.copy()
        
        to_encode.update({'exp': datetime.now(timezone.utc) +  timedelta(minutes=1)})
        token = jwt.encode(
                to_encode,
                key=settings.SECRET_KEY,
                algorithm=settings.ALGORITHM)
        
        return token
    
    @staticmethod
    def generate_refresh_access_token(data: dict, expires_timedelta: timedelta):
        """
            this is the refresh token, after the token has been expired
        :param data:
            This is the data that will encode in the token
        :param expires_timedelta:
            This is the expiration of the token
        :return:
            the encoded token
        """
        to_encode = data.copy()
        expires = (datetime.now(timezone.utc) + expires_timedelta
                   if expires_timedelta else timedelta(days=5))
        
        to_encode.update({'exp': expires})
        token = jwt.encode(
                to_encode,
                key=settings.SECRET_KEY,
                algorithm=settings.ALGORITHM)
        
        return token
    
    @staticmethod
    def decode_generated_token(token : str):
        try:
            payload = jwt.decode(token,key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            if not payload:
                raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='Invalid credentials!',
                        headers={'WWW-Authenticate': 'Bearer'}
                )
           
            
        except JWTError as e:
            raise e
        
        user_data = TokenData(user_id=payload['user_id'], username=payload['username'])
        if not user_data:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Invalid credentials!',
                    headers={'WWW-Authenticate': 'Bearer'}
            )
        
        return user_data
    
    @staticmethod
    @asynccontextmanager
    async def lifespan(app):
        print(f'Server is starting at port {settings.PORT}...')
        yield
        print('Server has been shutdown.')
    
    @staticmethod
    def hash_user_password(plain_pass: str):
        if not plain_pass:
            return False
        
        return contex_password.hash(plain_pass)
    
    @staticmethod
    def verify_user_password(plain_pass, hashed_pass):
        try:
            return contex_password.verify(secret=plain_pass, hash=hashed_pass)
        
        except Argon2Error as e:
            print(f'An error occurred {e}!')
            return False
    
    @staticmethod
    def get_user_data(result_query: dict):
        if not result_query:
            return False
        return UserInDB(**result_query)
    @staticmethod
    def authenticate_user(result_query: dict, password: str):
        if not result_query:
            return False
        
        if not Utility.verify_user_password(
                plain_pass=password,
                hashed_pass=result_query['hash_password']):
            return False
        
        return True
    
    
    @staticmethod
    async def email_message(message: str, email, subject, subtype):
        
        code = generate_code.now()
        ''
        schema = MessageSchema(
                recipients=email,
                subject=subject,
                body=message,
                subtype=subtype
        )
    
        