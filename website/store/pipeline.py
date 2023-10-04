# yourapp/pipeline.py

from social_core.exceptions import AuthAlreadyAssociated
from social_core.exceptions import AuthFailed

def get_email(strategy, details, response, user=None, *args, **kwargs):
    if user:
        return
    if not details.get('email'):
        email = response.get('email')  # Change 'email' to the appropriate key in the API response
        if email:
            details['email'] = email
        else:
            raise AuthFailed(strategy.backend, 'Email not provided by the provider.')

def associate_by_email(strategy, details, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    email = details.get('email')

    if email:
        users = list(strategy.storage.user.get_users_by_email(email))
        if len(users) > 0:
            return {'is_new': False, 'user': users[0]}
        return {'is_new': True}

def user_details(strategy, details, user=None, *args, **kwargs):
    """Update user details using data from provider."""
    if user:
        changed = False  # flag to track changes
        for name, value in details.items():
            if value and getattr(user, name, None) != value:
                setattr(user, name, value)
                changed = True

        if changed:
            strategy.storage.user.changed(user)
