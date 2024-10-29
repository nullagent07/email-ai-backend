from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.gmail_auth import verify_gmail_token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post(
    "/assistants/email/gmail",
    status_code=status.HTTP_200_OK
)
async def email_assistant(
    token: str = Depends(oauth2_scheme)
):
    """
    Проверяет валидность Gmail токена
    
    Args:
        token: Gmail access token из заголовка Authorization: Bearer {token}
        
    Returns:
        dict: Сообщение об успешной проверке токена
        
    Raises:
        HTTPException: 
            - 401: Если Gmail токен невалиден
            - 500: При внутренней ошибке сервера
    """
    try:
        result = await verify_gmail_token(token)
        print(result)
        return {"status": "success", "message": "Gmail токен валиден"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
