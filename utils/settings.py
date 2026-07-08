from models import Setting, db


CALENDAR_TOKEN_KEY = "calendar_token"


def get_setting(key, default=None):
    setting = Setting.query.get(key)
    return setting.value if setting else default


def set_setting(key, value):
    setting = Setting.query.get(key)
    if setting is None:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    else:
        setting.value = value
    db.session.commit()


def delete_setting(key):
    setting = Setting.query.get(key)
    if setting is not None:
        db.session.delete(setting)
        db.session.commit()
