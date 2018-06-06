from slackclient import SlackClient

class State:
    def __init__(self):
        self.channels = []
        self.dms = []
        self.groups = []
        self.messages = []
        self.users = []
        self.pin_count = 0
        self.has_more = False
        self.is_limited = False
        self.profile_user_id = None

class Cache:
    def __init__(self):
        self.avatar = {}

class Store:
    def __init__(self, slack_token):
        self.slack_token = slack_token
        self.slack = SlackClient(slack_token)
        self.state = State()
        self.cache = Cache()

    def find_user_by_id(self, user_id):
        return self._users_dict.get(user_id)

    def load_auth(self):
        self.state.auth = self.slack.api_call('auth.test')

    def load_messages(self, channel_id):
        history = self.slack.api_call(
            'conversations.history',
            channel=channel_id
        )
        self.state.messages = history['messages']
        self.state.has_more = history.get('has_more', False)
        self.state.is_limited = history.get('is_limited', False)
        self.state.pin_count = history['pin_count']
        self.state.messages.reverse()

    def load_channel(self, channel_id):
        if channel_id[0] == 'G':
            self.state.channel = self.slack.api_call(
                'groups.info',
                channel=channel_id
            )['group']
        elif channel_id[0] == 'C':
            self.state.channel = self.slack.api_call(
                'channels.info',
                channel=channel_id
            )['channel']

    def load_channels(self):
        conversations = self.slack.api_call(
            'users.conversations',
            exclude_archived=True,
            types='public_channel,private_channel,im'
        )['channels']
        for channel in conversations:
            # Public channel
            if channel.get('is_channel', False):
                self.state.channels.append(channel)
            # Private channel
            elif channel.get('is_group', False):
                self.state.channels.append(channel)
            # Direct message
            elif channel.get('is_im', False):
                self.state.dms.append(channel)
        self.state.channels.sort(key=lambda channel: channel['name'])
        self.state.dms.sort(key=lambda dm: dm['created'])

    def load_groups(self):
        self.state.groups = self.slack.api_call('mpim.list')['groups']

    def load_users(self):
        self.state.users = list(filter(
            lambda user: not user.get('deleted', False),
            self.slack.api_call('users.list')['members']
        ))
        self._users_dict = {}
        self._bots_dict = {}
        for user in self.state.users:
            if user.get('is_bot', False):
                self._users_dict[user['profile']['bot_id']] = user
            self._users_dict[user['id']] = user
