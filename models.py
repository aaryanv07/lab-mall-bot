from pydantic import BaseModel
from typing import Optional

# We now only have ONE model because we merged everything into the products table
class Product(BaseModel):
    id: int
    code_no: Optional[str] = None
    title: str
    pack_size: Optional[str] = None
    make: Optional[str] = None
    price: float = 0.0
    hsn_code: Optional[str] = None
    tax_percent: Optional[float] = 0.0