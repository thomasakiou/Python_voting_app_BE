from sqlalchemy.orm import Session
from ..domain import user as models
from .utils import hash_password
from .config import SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, SUPER_ADMIN_FULLNAME

def init_super_admin(db: Session):
    existing_user = db.query(models.User).filter(models.User.username == SUPER_ADMIN_USERNAME).first()
    if not existing_user:
        super_admin = models.User(
            username=SUPER_ADMIN_USERNAME,
            full_name=SUPER_ADMIN_FULLNAME,
            password=hash_password(SUPER_ADMIN_PASSWORD),
            role="super-admin",
            must_change_password=False
        )
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        print("Super admin created")
    else:
        print("ℹSuper admin already exists")
