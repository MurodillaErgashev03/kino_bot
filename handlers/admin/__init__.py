from aiogram import Router

admin_router = Router(name="admin")

from . import panel
from . import film
from . import serial
from . import admin_manage
from . import subscription
from . import advertising
from . import channel_post
