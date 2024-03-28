from sqlalchemy import Column, Integer, String, Float
from database import Base

class FoodItem(Base):
    # Add more fields as necessaryclass FoodItem(Base):
    __tablename__ = 'food_items'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # Specify length here
    description = Column(String(255), nullable=True)  # And here
    price = Column(Float, nullable=False)