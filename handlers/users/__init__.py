from aiogram import Router

user_router = Router(name="user")

from . import start
from . import help
from . import about
from . import echo
