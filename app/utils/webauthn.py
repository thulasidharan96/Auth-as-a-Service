import json
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response, options_to_json
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential, AuthenticatorSelectionCriteria, UserVerificationRequirement, ResidentKeyRequirement
from app.core.config import settings
from typing import Any, Tuple

# In-memory storage for challenges (in production, use Redis)
challenge_store = {}

def get_registration_options(user_id: str, email: str) -> dict:
    options = generate_registration_options(
        rp_id=settings.RP_ID,
        rp_name=settings.RP_NAME,
        user_id=user_id.encode(),
        user_name=email,
        user_display_name=email,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    challenge_store[user_id] = options.challenge
    return json.loads(options_to_json(options))

def verify_registration(user_id: str, credential_response: Any) -> Tuple[str, str, int]:
    challenge = challenge_store.pop(user_id, None)
    if not challenge:
        raise Exception("Challenge not found")
        
    verification = verify_registration_response(
        credential=credential_response,
        expected_challenge=challenge,
        expected_rp_id=settings.RP_ID,
        expected_origin=settings.ORIGIN,
    )
    
    return verification.credential_id.hex(), verification.credential_public_key.hex(), verification.sign_count

def get_authentication_options(email: str) -> dict:
    options = generate_authentication_options(
        rp_id=settings.RP_ID,
        user_verification=UserVerificationRequirement.PREFERRED
    )
    challenge_store[email] = options.challenge
    return json.loads(options_to_json(options))

def verify_authentication(email: str, credential_response: Any, public_key: str, sign_count: int) -> int:
    challenge = challenge_store.pop(email, None)
    if not challenge:
        raise Exception("Challenge not found")
        
    verification = verify_authentication_response(
        credential=credential_response,
        expected_challenge=challenge,
        expected_rp_id=settings.RP_ID,
        expected_origin=settings.ORIGIN,
        credential_public_key=bytes.fromhex(public_key),
        credential_current_sign_count=sign_count,
    )
    
    return verification.new_sign_count
