from environs import Env

env = Env()
env.read_env()
host = env.str('host')
user = env.str('user')
password = env.str('password')
database = env.str('database')

BOT_TOKEN = env.str('BOT_TOKEN')
# ADMINS = env.list('ADMINS')

