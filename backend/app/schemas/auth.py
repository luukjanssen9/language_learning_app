from pydantic import BaseModel


class GoogleSignIn(BaseModel):
    """Request body for POST /auth/google -- the signed ID-token JWT the
    Google Identity Services button hands back to the frontend.
    """

    credential: str
