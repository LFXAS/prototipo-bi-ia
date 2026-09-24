from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base comun para modelos internos y del datamart."""


# Las importaciones hacen que Alembic conozca los modelos de los módulos.
from app.modules.copilot import models as copilot_models  # noqa: E402, F401
from app.modules.etl import models as etl_models  # noqa: E402, F401
from app.modules.metadata import models as metadata_models  # noqa: E402, F401
from app.modules.parameters import models as parameter_models  # noqa: E402, F401
from app.modules.security import models as security_models  # noqa: E402, F401
