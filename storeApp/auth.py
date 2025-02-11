from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Security, status
import jwt
import datetime
from database import find_user
import logging
logging.basicConfig(level=logging.DEBUG)



class AuthHandler:
    security = HTTPBearer()
    secret = 'supersecret'
    # Add this above the line where bcrypt is used
    logging.debug("Attempting to hash password using bcrypt...")
   

    # Define password hashing context using bcrypt
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    token_blacklist = set()

    # Hash the password with bcrypt
    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    # Verify the password against a hashed password
    def verify_password(self, pwd: str, hashed_pwd: str) -> bool:
        logging.debug(f"Verifying password: {pwd} against hashed: {hashed_pwd}")
        result = self.pwd_context.verify(pwd, hashed_pwd)
        logging.debug(f"Password verification result: {result}")
        return result


    # Encode a JWT token with a user ID and expiration
    def encode_token(self, user_id: str) -> str:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, self.secret, algorithm='HS256')

    # Decode a JWT token
    def decode_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Expired signature')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid token')

    # Wrapper to decode token from authorization header
    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_token(auth.credentials)

    # Retrieve the current user from the token
    def get_current_user(self, auth: HTTPAuthorizationCredentials = Security(security)):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials'
            )

            username = self.decode_token(auth.credentials)
            print(f"Decoded Username: {username}")  # Debugging
            
            if username is None:
                raise credentials_exception
            
            user = find_user(username)
            print(f"Found User: {user}")  # Debugging
            
            if user is None:
                raise credentials_exception
            
            return user  


    
    
     # Blacklist a token
    def blacklist_token(self, token: str):
        self.token_blacklist.add(token)

    # Check if a token is blacklisted
    def is_token_blacklisted(self, token: str) -> bool:
        return token in self.token_blacklist