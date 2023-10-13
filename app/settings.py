import mysql.connector


SECRET_KEY = "e7+QvUUa5l5olKDcizR0rHok7KHSUxAT92XBsVWW9LNSJ2iLhTf7MeOYZFzXYrD7yFHBV3diloQtLvCyaFx0SQ=="
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
CONNECTION = mysql.connector.connect(
  host="localhost",
  user="root",
  password="!7EE5#Pe1d@J",
  port="3306",
  database='gambledb'
)

CURSOR = CONNECTION.cursor()