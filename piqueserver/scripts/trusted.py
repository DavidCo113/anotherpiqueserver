"""
Adds the ability to 'trust' certain players, i.e. they cannot be votekicked
or rubberbanded.

Commands
^^^^^^^^

* ``/trust <player>`` gives trusted status to a player

.. codeauthor:: mat^2 & hompy
"""

from piqueserver.commands import command, admin, get_player

S_GRANTED = '{player} is now trusted'
S_GRANTED_SELF = "You've been granted trust, and can't be votekicked"
S_CANT_VOTEKICK = "{player} is trusted and can't be votekicked"
S_RESULT_TRUSTED = 'Trusted user'


@command(admin_only=True)
def trust(connection, player):
    player = get_player(connection.protocol, player)
    player.on_user_login(['trusted'], False)
    auth = connection.protocol.auth_backend
    auth.set_user_type(player, 'trusted')
    player.send_chat(S_GRANTED_SELF)
    return S_GRANTED.format(player=player.name)


def apply_script(protocol, connection, config):
    class TrustedConnection(connection):

        def on_user_login(self, user_types, verbose=True):
            if 'trusted' in user_types:
                self.speedhack_detect = False
                votekick = getattr(self.protocol, 'votekick', None)
                if votekick and votekick.victim is self:
                    votekick.end(S_RESULT_TRUSTED)
                    self.protocol.votekick = None
            return connection.on_user_login(self, user_types, verbose)

    class TrustedProtocol(protocol):

        def on_votekick_start(self, instigator, victim, reason):
            if victim.user_types.trusted:
                return S_CANT_VOTEKICK.format(player=victim.name)
            return protocol.on_votekick_start(self, instigator, victim, reason)

    return TrustedProtocol, TrustedConnection
