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

    def getUser(self, username):
        """Gets the a user by using a username key from the temporary
        users dict
        """
        return self.users.get(username, None)

    def addUser(self, user):
        """Add a new user in the user's temporary collection using his username
        as the key"""
        if user.username not in self.users:
            self.users[user.username] = user
        else:
            raise KeyError('User %s already exists.' % user.username)

    def delUser(self, user):
        """Remove a user from the user's temporary collection using a username 
        as the key"""
        user = None
        if isinstance(user, str):
            user = self.getUser(user)
        try:
            del self.users[user.username]
        except KeyError:
            pass
        return user

