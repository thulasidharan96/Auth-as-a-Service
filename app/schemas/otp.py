from pydantic import BaseModel

class OTPSetupResponse(BaseModel):
    secret: str
    uri: str

class OTPVerify(BaseModel):
    code: str
