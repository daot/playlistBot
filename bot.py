import configparser
import datetime
import json
import os
import re

import discord
import requests
import spotipy
import spotipy.util

client = discord.Client()


@client.event
async def on_ready():
    print('------')
    print('Logged in as: {}:{}'.format(client.user.name, client.user.id))
    print('------')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    scope = 'playlist-modify-public'
    token = spotipy.util.prompt_for_user_token(config['DEFAULT']['spotify_username'], scope=scope, client_id=config['DEFAULT']['spotify_client_id'], client_secret=config['DEFAULT']['spotify_client_secret'], redirect_uri="http://scooterlabs.com/echo")
    sp = spotipy.Spotify(auth=token)
    sp.trace = False

    def editPlaylist(url, action):
        print(str(datetime.datetime.now()) + ': Getting Tracks...')

        try:
            j = json.loads(requests.get('https://api.song.link/v1-alpha.1/links?url={}&userCountry=US'.format(url)).text)
            print('{}: {}'.format(str(datetime.datetime.now()), [item for item in j["entitiesByUniqueId"]]))
            for item in j['entitiesByUniqueId']:
                if "SPOTIFY" in item:
                    if "SPOTIFY.COM/TRACK" not in url.upper():
                        type = j['entitiesByUniqueId'][item]['type']
                        if 'album' in type:
                            return "This is an album not a track"

                    title = j['entitiesByUniqueId'][item]['title']
                    artist = j['entitiesByUniqueId'][item]['artistName']

                    if "SPOTIFY.COM/TRACK" in url.upper():
                        id = url.split('/')[4].split('?')[0]
                    else:
                        id = j['entitiesByUniqueId'][item]['id']

                    print('{}: ID: {}'.format(str(datetime.datetime.now()), id))

                    art = j['entitiesByUniqueId'][item]['thumbnailUrl']

            sp.user_playlist_remove_all_occurrences_of_tracks(user=config['DEFAULT']['spotify_username'], playlist_id=config['DEFAULT']['spotify_playlist_id'], tracks=[id])
            if action == 0:
                sp.user_playlist_add_tracks(user=config['DEFAULT']['spotify_username'], playlist_id=config['DEFAULT']['spotify_playlist_id'], tracks=[id])
                print(str(datetime.datetime.now()) + ": Added {} by {} to the Playlist".format(title, artist))
                return [title, artist, art]
            elif action == 1:
                return "Track Successfully Deleted"
        except UnboundLocalError:
            print(str(datetime.datetime.now()) + ': Spotify URL Not Found')
            return "Spotify URL Not Found"
        except KeyError:
            print(str(datetime.datetime.now()) + ': Invalid Song Url')
            return "Invalid Song Url"
        except Exception as e:
            print(str(datetime.datetime.now()) + ': Unknown Error: ' + str(e))
            return "Unknown Error: " + str(e)

    gotlink = 0
    if str(message.channel.id) == str(config['DEFAULT']['discord_channel']):
        for word in message.content.split(" "):
            if re.match('HTTPS?://', word.upper()) is not None:
                gotlink = 1
                if message.content.upper().startswith('!DEL'):
                    if config['DEFAULT']['moderator_role'].upper() in [y.name.upper() for y in message.author.roles]:
                        embed = discord.Embed(color=0x1ed760)
                        embed.set_author(name=editPlaylist(word, 1), url="https://open.spotify.com/playlist/{}".format(config['DEFAULT']['spotify_playlist_id']), icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png")
                        await message.channel.send(embed=embed)
                    else:
                        embed = discord.Embed(color=0x1ed760)
                        embed.set_author(name="User Not Authorized to Delete Songs", url="https://open.spotify.com/playlist/{}".format(config['DEFAULT']['spotify_playlist_id']), icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png")
                        await message.channel.send(embed=embed)
                else:
                    m = editPlaylist(word, 0)
                    if len(m) == 3:
                        embed = discord.Embed(color=0x1ed760)
                        embed.set_author(name="Successfully Added to the Playlist", url="https://open.spotify.com/playlist/{}".format(config['DEFAULT']['spotify_playlist_id']), icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png")
                        embed.add_field(name='Title:', value=m[0])
                        embed.add_field(name='Artist:', value=m[1], inline=False)
                        embed.set_thumbnail(url=m[2])
                        await message.channel.send(embed=embed)
                    else:
                        embed = discord.Embed(color=0x1ed760)
                        embed.set_author(name=m, url="https://open.spotify.com/playlist/{}".format(config['DEFAULT']['spotify_playlist_id']), icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png")
                        await message.channel.send(embed=embed)

        if gotlink == 0:
            await message.delete()
            embed = discord.Embed(color=0x1ed760)
            embed.set_author(name="Only Links Are Allowed", url="https://open.spotify.com/playlist/{}".format(config['DEFAULT']['spotify_playlist_id']), icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png")
            response = await message.channel.send(embed=embed)
            await response.delete(delay=3)

if __name__ == '__main__':
    if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.txt')):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.txt'))
        client.run(config['DEFAULT']['discord_token'])
    else:
        print('Unable to find "config.txt"')
        print('Please download it from the repository')
