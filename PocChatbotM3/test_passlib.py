from passlib.context import CryptContext
import logging

logging.basicConfig(level=logging.INFO)

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash = pwd_context.hash("test")
    logging.info(f"Hash generated: {hash}")
    verify = pwd_context.verify("test", hash)
    logging.info(f"Verification: {verify}")
except Exception as e:
    logging.error(f"Error: {e}")
