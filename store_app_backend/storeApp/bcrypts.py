import bcrypt

# Hash a password
password = b"test_password"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())

# Verify the password
if bcrypt.checkpw(password, hashed):
    print("Password matches")
else:
    print("Password does not match")
