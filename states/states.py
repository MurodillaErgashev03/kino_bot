from aiogram.filters.state import State, StatesGroup


class FilmStates(StatesGroup):
    kod = State()
    kod_delete = State()
    chekk = State()
    film_id = State()
    film_name = State()
    film_banner = State()


class SerialStates(StatesGroup):
    waiting_for_serial_name = State()
    waiting_for_serial_title = State()
    waiting_for_serial_banner = State()
    waiting_for_episode_video = State()
    waiting_for_more_episodes = State()
    waiting_for_confirmation = State()
    waiting_for_serial_delete = State()
    waiting_for_episode_video_existing = State()
    waiting_for_more_episodes_existing_serial = State()


class AdminStates(StatesGroup):
    admin_chat_id = State()


class SubscriptionStates(StatesGroup):
    chat_id = State()
    waiting_for_channel_username = State()
    waiting_for_channel_chat_id = State()
    waiting_for_channel_link = State()
    waiting_for_group_url = State()
    waiting_for_group_chat_id = State()
    waiting_for_instagram_username = State()


class AdStates(StatesGroup):
    ask_ad_content = State()
    ask_ad_duration = State()
    ask_ad_custom_hours = State()


class ChannelPostStates(StatesGroup):
    waiting_for_channel_selection = State()
