from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import User, OAuthCredentials
from app.utils.gmail_auth import verify_gmail_token
from app.core import security
from datetime import timedelta, datetime

router = APIRouter()

@router.post("/login/gmail")
async def login_via_gmail(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Авторизация через Gmail SSO
    """
    try:
        # Проверяем токен и получаем информацию о пользователе
        token_info = await verify_gmail_token(token)
        
        if not token_info['valid']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен Gmail"
            )
            
        # Ищем пользователя по email из токена
        oauth_creds = db.query(OAuthCredentials).filter(
            OAuthCredentials.email == token_info['email'],
            OAuthCredentials.provider == 'google'
        ).first()
        
        if oauth_creds:
            # Обновляем токены
            oauth_creds.access_token = token_info['access_token']
            oauth_creds.expires_at = datetime.utcnow() + timedelta(seconds=token_info['expires_in'])
            user = oauth_creds.user
        else:
            # Создаем нового пользователя
            user = User(
                email=token_info['email'],
                name=token_info['name'],
                is_active=True
            )
            db.add(user)
            db.flush()
            
            # Создаем запись OAuth
            oauth_creds = OAuthCredentials(
                user_id=user.id,
                provider='google',
                email=token_info['email'],
                access_token=token_info['access_token'],
                expires_at=datetime.utcnow() + timedelta(seconds=token_info['expires_in'])
            )
            db.add(oauth_creds)
            
        db.commit()
        
        # Создаем JWT токен для нашего приложения
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Ошибка авторизации: {str(e)}"
        )
