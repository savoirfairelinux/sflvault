"""The application's Globals object"""
from pylons import config

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application
    """

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the 'g'
        variable
        """
        self.users = {}

    def get_user(self, username):
        """Gets the a user by using a username key from the temporary
        users dict
        """
        return self.users.get(username, None)

    def add_user(self, user):
        """Add a new user in the user's temporary collection using his username
        as the key"""
        if user.username not in self.users:
            self.users[user.username] = user
        else:
            raise KeyError('User %s already exists.' % user.username)

    def del_user(self, user):
        """Remove a user from the user's temporary collection using a username 
        as the key.

        Either the User object or username is accepted.

        Returns the User object if it was present.
        """
        if isinstance(user, str):
            username = user
            user = self.get_user(user)
        else:
            username = user.username

        if username in self.users:
            del self.users[username]

        return user

