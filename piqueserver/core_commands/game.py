import math
import re
from twisted.internet import reactor
from piqueserver.config import cast_duration
from pyspades.common import prettify_timespan
from piqueserver.commands import (
    command, CommandError, get_player, get_team, get_truthy, target_player)


@command('time')
def get_time_limit(connection):
    """
    Tell you the current time limit
    /time
    """
    advance_call = connection.protocol.advance_call
    if advance_call is None:
        return 'No time limit set'
    left = int(
        math.ceil((advance_call.getTime() - reactor.seconds()) / 60.0))
    return 'There are %s minutes left' % left


@command("resetgame", admin_only=True)
def reset_game(connection):
    """
    Reset the game
    /resetgame
    """
    resetting_player = connection
    # irc compatibility
    if resetting_player not in connection.protocol.players.values():
        for player in connection.protocol.players.values():
            resetting_player = player
            if player.admin:
                break
        if resetting_player is connection:
            return
    connection.protocol.reset_game(resetting_player)
    connection.protocol.on_game_end()
    connection.protocol.broadcast_chat(
        'Game has been reset by %s' % connection.name,
        irc=True)


@command(admin_only=True)
def lock(connection, value):
    """
    Make a specified team no longer joinable until it's unlocked
    /lock <blue|green|spectator>
    New players will be placed in the spectator team even if it's locked
    """
    team = get_team(connection, value)
    team.locked = True
    connection.protocol.broadcast_chat('%s team is now locked' % team.name)
    connection.protocol.irc_say('* %s locked %s team' % (connection.name,
                                                         team.name))


@command(admin_only=True)
def unlock(connection, value):
    """
    Unlock a team
    /unlock <blue|green|spectator>
    """
    team = get_team(connection, value)
    team.locked = False
    connection.protocol.broadcast_chat('%s team is now unlocked' % team.name)
    connection.protocol.irc_say('* %s unlocked %s team' % (connection.name,
                                                           team.name))
@command(admin_only=True)
@target_player
def switch(connection, player, team=None):
    """
    Switch teams either for yourself or for a given player
    /switch [player] [team]
    """
    protocol = connection.protocol
    new_team = protocol.blue_team
    old_team = player.team

    if not player.team.spectator:
        new_team = player.team.other

    if team:
        new_team = get_team(connection, team)

    if player.invisible:
        player.drop_intel() # this shouldn't ever be possible, but just in case
        player.team = new_team
        player.on_team_changed(old_team)
        player.spawn(player.world_object.position.get())
        player.send_chat('Switched to %s team' % player.team.name)
        if (connection is not player
                and connection in protocol.players.values()):
            connection.send_chat('Switched %s to %s team' % (player.name,
                                                             player.team.name))
        protocol.irc_say('* %s silently switched teams' % player.name)
    else:
        if old_team.spectator:
            player.team = new_team
            player.on_team_changed(old_team)
            player.spawn()
        else:
            player.respawn_time = protocol.respawn_time
            player.set_team(new_team)
        protocol.broadcast_chat('%s switched teams' % player.name, irc=True)

@command('setbalance', admin_only=True)
def set_balance(connection, value):
    """
    Turn automatic balancing on or off
    /setbalance <on|off>
    """
    should_balance = get_truthy(value)
    if should_balance is None:
        raise CommandError()

    protocol = connection.protocol
    protocol.balanced_teams = should_balance

    if should_balance:
        protocol.broadcast_chat('now balancing teams')
        connection.protocol.irc_say(
            '* %s turned on balanced teams' % connection.name)
    else:
        protocol.broadcast_chat('now no longer balancing teams')
        connection.protocol.irc_say(
            '* %s turned off balanced teams' % connection.name)


@command('togglebuild', 'tb', admin_only=True)
def toggle_build(connection, player=None):
    """
    Toggle building for everyone in the server or for a given player
    /togglebuild [player]
    """
    if player is not None:
        player = get_player(connection.protocol, player)
        value = not player.building
        player.building = value
        msg = '%s can build again' if value else '%s is disabled from building'
        connection.protocol.broadcast_chat(msg % player.name)
        connection.protocol.irc_say('* %s %s building for %s' %
                                    (connection.name,
                                     ['disabled', 'enabled'][int(value)],
                                     player.name))
    else:
        value = not connection.protocol.building
        connection.protocol.building = value
        on_off = ['OFF', 'ON'][int(value)]
        connection.protocol.broadcast_chat(
            'Building has been toggled %s!' % on_off)
        connection.protocol.irc_say(
            '* %s toggled building %s' % (connection.name,
                                          on_off))


@command('allowbuild', 'ab', admin_only=True)
def allow_build(connection, player=None):
    """
    Allow building for everyone in the server or for a given player
    /allowbuild [player]
    """
    if player is not None:
        player = get_player(connection.protocol, player)
        player.building = True
        msg = '%s can build again'
        connection.protocol.broadcast_chat(msg % player.name)
        connection.protocol.irc_say('* %s enabled building for %s' %
                                    (connection.name, player.name))
    else:
        connection.protocol.building = True
        connection.protocol.broadcast_chat('Building has been toggled ON!')
        connection.protocol.irc_say(
            '* %s toggled building ON' % connection.name)


@command('disablebuild', 'db', admin_only=True)
def disable_build(connection, player=None):
    """
    Disable building for everyone in the server or for a given player
    /disablebuild [player]
    """
    if player is not None:
        player = get_player(connection.protocol, player)
        player.building = False
        msg = '%s is disabled from building'
        connection.protocol.broadcast_chat(msg % player.name)
        connection.protocol.irc_say('* %s disabled building for %s' %
                                    (connection.name, player.name))
    else:
        connection.protocol.building = False
        connection.protocol.broadcast_chat('Building has been toggled OFF!')
        connection.protocol.irc_say(
            '* %s toggled building OFF' % connection.name)


@command('togglekill', 'tk', admin_only=True)
def toggle_kill(connection, player=None):
    """
    Toggle killing for everyone in the server or for a given player
    /togglekill [player]
    """
    if player is not None:
        player = get_player(connection.protocol, player)
        value = not player.killing
        player.killing = value
        msg = '%s can kill again' if value else '%s is disabled from killing'
        connection.protocol.broadcast_chat(msg % player.name)
        connection.protocol.irc_say('* %s %s killing for %s' %
                                    (connection.name,
                                     ['disabled', 'enabled'][int(value)],
                                     player.name))
    else:
        value = not connection.protocol.killing
        connection.protocol.killing = value
        on_off = ['OFF', 'ON'][int(value)]
        connection.protocol.broadcast_chat(
            'Killing has been toggled %s!' % on_off)
        connection.protocol.irc_say(
            '* %s toggled killing %s' % (connection.name,
                                         on_off))


@command('toggleteamkill', 'ttk', admin_only=True)
def toggle_teamkill(connection, player=None):
    """
    Toggle friendly fire for everyone in the server or for a given player
    /toggleteamkill [player]
    """
    if player is not None:
        player = get_player(connection.protocol, player)
        value = not player.friendly_fire
        player.friendly_fire = value
        msg = '%s can teamkill again' if value else '%s is disabled from teamkilling'
        connection.protocol.broadcast_chat(msg % player.name)
        connection.protocol.irc_say('* %s %s friendly fire for %s' %
                                    (connection.name,
                                     ['disabled', 'enabled'][int(value)], player.name))
    else:
        value = not connection.protocol.friendly_fire
        connection.protocol.friendly_fire = value
        on_off = 'ON' if value else 'OFF'
        if not value:
            connection.protocol.friendly_fire_on_grief = False

        connection.protocol.broadcast_chat(
            'Friendly fire has been toggled %s!' % on_off)
        connection.protocol.irc_say('* %s toggled friendly fire %s' % (
            connection.name, on_off))


@command('togglegriefteamkill', 'tgtk', admin_only=True)
def grief_teamkill(connection):
    value = not connection.protocol.friendly_fire_on_grief
    connection.protocol.friendly_fire_on_grief = value
    on_off = 'ON' if value else 'OFF'
    connection.protocol.broadcast_chat(f'Friendly fire on grief has been toggled {on_off}')
    connection.protocol.irc_say(f'* {connection.name} toggled friendly fire on grief {on_off}')


@command('allowteamkill', 'atk', admin_only=True)
def allow_teamkill(connection, player = None):
    if player is not None:
        player = get_player(connection.protocol, player)
        player.friendly_fire = True
        msg = '%s can teamkill again'
        connection.protocol.broadcast_chat(msg % player.name)
        connection.protocol.irc_say('* %s enabled teamkilling for %s' % (connection.name,
            player.name))
    else:
        connection.protocol.friendly_fire = True
        connection.protocol.broadcast_chat('Friendly fire has been toggled ON!')
        connection.protocol.irc_say('* %s toggled friendly fire ON' % connection.name)


@command('disableteamkill', 'dtk', admin_only=True)
def disable_teamkill(connection, player = None):
    if player is not None:
        player = get_player(connection.protocol, player)
        player.friendly_fire = False
        msg = '%s is disabled from teamkilling'
        connection.protocol.broadcast_chat(msg % player.name)
        connection.protocol.irc_say('* %s disabled teamkilling for %s' % (connection.name,
            player.name))
    else:
        connection.protocol.friendly_fire = False
        connection.protocol.broadcast_chat('Friendly fire has been toggled OFF!')
        connection.protocol.irc_say('* %s toggled friendly fire OFF' % connection.name)


@command('globalchat', admin_only=True)
def global_chat(connection, value=None):
    """
    Enable or disable global chat
    /globalchat [on|off]
    Toggles if no arguments are given
    """
    enabled = get_truthy(value)
    if enabled is True:
        connection.protocol.global_chat = True
    elif enabled is False:
        connection.protocol.global_chat = False
    else:
        connection.protocol.global_chat = not connection.protocol.global_chat

    connection.protocol.broadcast_chat(
        'Global chat %s' % (
            'enabled' if connection.protocol.global_chat else 'disabled'),
        irc=True)


@command('timelimit', admin_only=True)
def set_time_limit(connection, duration):
    """
    Set this game time limit
    /timelimit <duration>
    """
    limit = cast_duration(duration)
    span = prettify_timespan(limit)
    protocol = connection.protocol
    # takes time in minutes
    protocol.set_time_limit(limit/60)
    protocol.broadcast_chat('Time limit set to {}'.format(span), irc=True)


@command(admin_only=True)
def fog(connection, *args):
    """
    Set the fog color
    /fog red green blue (all values 0-255)
    /fog #aabbcc        (hex representation of rgb)
    /fog #abc           (short hex representation of rgb)
    """
    if (len(args) == 3):
        r = int(args[0])
        g = int(args[1])
        b = int(args[2])
    elif (len(args) == 1 and args[0][0] == '#'):
        hex_code = args[0][1:]

        if (len(hex_code) != 3) and (len(hex_code) != 6):
            raise ValueError("Invalid hex code length")

        # it's a short hex code, turn it into a full one
        if len(hex_code) == 3:
            hex_code = (hex_code[0]*2) + (hex_code[1]*2) + (hex_code[2]*2)

        valid_characters = re.compile('[a-fA-F0-9]')
        for char in hex_code:
            if valid_characters.match(char) is None:
                raise ValueError("Invalid hex code characters")

        r = int(hex_code[0:2], base=16)
        g = int(hex_code[2:4], base=16)
        b = int(hex_code[4:6], base=16)
    else:
        raise ValueError("Neither RGB or hex code provided")

    old_fog_color = connection.protocol.fog_color
    connection.protocol.set_fog_color((r, g, b))
    if old_fog_color == (r, g, b):
        return ('Fog color changed successfully\n'
                'Warning: fog color set to same color as before')
    return 'Fog color changed successfully'


@command(admin_only=True)
def resetfog(connection):
    protocol = connection.protocol

    protocol.set_fog_color(
        getattr(protocol.map_info.info, 'fog', protocol.default_fog)
    )

    return 'Fog color reset'
