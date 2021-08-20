import jwt as _jwt

if _jwt.__version__ >= "2.0.0":
    jwt_encode = _jwt.encode
else:

    def jwt_encode(*args, **kwargs) -> str:
        encoded = _jwt.encode(*args, **kwargs)
        return encoded.decode()  # bytestring to string
