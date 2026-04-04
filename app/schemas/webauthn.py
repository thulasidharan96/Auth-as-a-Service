from pydantic import BaseModel
from typing import Any

class WebauthnRegistrationStart(BaseModel):
    pass

class WebauthnLoginStart(BaseModel):
    email: str
    
class WebauthnRegistrationFinish(BaseModel):
    response: Any
    
class WebauthnLoginFinish(BaseModel):
    email: str
    response: Any
