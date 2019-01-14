# coding: utf-8
# This code is not endorsed nor approved by the site maintainers or any representatives.
# Use at your own risk.
# The plugin was based on the work of https://github.com/flightlevel/TehConnectionCouchPotatoPlugin/ and
# https://github.com/djoole/couchpotato.provider.t411
# most credits goes to them
from bs4 import BeautifulSoup

from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from requests import HTTPError
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider
from couchpotato.core.helpers.variable import getImdb
import traceback
import re
import time

log = CPLog(__name__)
torrentlist = []


class TorrentDetails(object):
    def __init__(self, seeders, leechers, permalink, downlink, torrentid, torrentname, filesize, freeleech,
                 torrentscore, datetorrentadded, ageindays):
        self.seeders = seeders
        self.leechers = leechers
        self.permalink = permalink
        self.downlink = downlink
        self.torrentid = torrentid
        self.torrentname = torrentname
        self.filesize = filesize
        self.freeleech = freeleech
        self.torrentscore = torrentscore
        self.datetorrentadded = datetorrentadded
        self.ageindays = ageindays


class ManicomioShare(TorrentProvider, MovieProvider):
    # 'search': 'http://www.manicomio-share.com/busca-filmes.php?vince=0&onde=1&search=%s&parent_categ=0&qualite=&cor=&codecvideo=&extensao=&tipoaudio=&lang=0&paisorigem=&direc=',
    urls = {
        'baseurl': 'https://www.manicomio-share.com/',
        'login': 'https://www.manicomio-share.com/',
        'login_check': 'https://www.manicomio-share.com/deslogar.php',
        'search': 'https://www.manicomio-share.com/pesquisa.php?busca=%s&cat=%s&opt2=0&vnc=0&ano=%s&opt=%s',
        'torrentdetails': 'https://www.manicomio-share.com/ajax/ajax2.php?torrent=%s',
        'imdbreleaseinfo': 'http://www.imdb.com/title/%s/releaseinfo'
    }

    http_time_between_calls = 5  # seconds

    cat_ids = [
        ([127, 148], ['720p', '1080p', 'brrip']),
        ([147, 183], ['3d']),
        ([189, 193], ['4K', '2160p']),
        ([132, 143, 152], ['bdrip']),
        ([142], ['bd25', 'bd50']),
        ([34, 144], ['dvdrip', 'dvdr', 'dvd-rip']),
    ]

    def _searchOnTitle(self, title, movie, quality, results):
        log.info('SEARCH: Looking on manicomio-share for movie %s (%s), with quality %s' %
                 (title, movie['info']['year'], str(quality['custom']['quality'])))
        movieYear = int(movie['info']['year'])
        self.searchMovie(title, movie, quality, results,
                         torrentlist, movieYear)

        if len(torrentlist) is 0:
            # Hack to account for the braziilian launch dates that sometimes are a year delayed. Only used when
            # normal searching yields no results.
            log.info('Searching movie %s for year %s' %
                     (title, str(movieYear+1)))
            self.searchMovie(title, movie, quality, results,
                             torrentlist, movieYear + 1)

        log.info('Number of torrents found from manicomio-share = ' +
                 str(len(torrentlist)))

        for torrentfind in torrentlist:
            log.debug('Detalhes: leechers: ' + str(torrentfind.leechers)
                      + ' seeders: ' + str(torrentfind.seeders)
                      + ' name: ' +
                      self.replaceTitleAndValidateTorrent(
                          movie, torrentfind.torrentname)
                      + ' id: ' + str(torrentfind.torrentid)
                      + ' size: ' + str(self.parseSize(torrentfind.filesize))
                      + ' score: ' + str(torrentfind.torrentscore)
                      + ' date: ' + str(torrentfind.datetorrentadded)
                      + ' age: ' + str(torrentfind.ageindays)
                      #               + ' url: ' + str(torrentfind.downlink)
                      #               + ' detail_url: ' + str(torrentfind.permalink)
                      )

            results.append({
                'leechers': torrentfind.leechers,
                'seeders': torrentfind.seeders,
                'name': self.replaceTitleAndValidateTorrent(movie, torrentfind.torrentname),
                'url': torrentfind.downlink,
                'detail_url': torrentfind.permalink,
                'id': torrentfind.torrentid,
                'size': self.parseSize(torrentfind.filesize),
                'score': torrentfind.torrentscore,
                'date': torrentfind.datetorrentadded,
                'age': torrentfind.ageindays
            })

    def searchMovie(self, title, movie, quality, results, torrentlist, movieYear):
        # We remove any : simbols from the movie title to make our search more inclusive
        movieTitleWithoutColons = re.sub(':', "", title)
        
        if self.conf('only_freeleech'):
            onlyfreeleech = 1
        else:
            onlyfreeleech = 0
        #Search the site for every category code in cat_ids sequentially
        for categoryCode in self.getCatId(quality):
            data = self.getHTMLData(self.urls['search'] % (
                tryUrlencode(movieTitleWithoutColons), categoryCode, movieYear, onlyfreeleech))
        #Process the data returned by the search. It should be a html page with the various torrents
            if data:
                try:
                    #Try to get the main html table where the torrent list is located
                    resultsTable = BeautifulSoup(data).find(
                        'table', attrs={'id': 'tbltorrent'})
                    if resultsTable is None:
                        log.info(
                            'Movie not found on Manicomio-share. Maybe try an alternative name?')
                        continue
                    #Get the multiple torrent links in an array
                    htmltorrentlist = resultsTable.find_all(
                        'tr', attrs={'id': 'closest'})
                    if htmltorrentlist is None:
                        log.debug('Could not get torrents list')
                    #Process each individual torrent returned 
                    for torrent in htmltorrentlist:
                        torrentdata = TorrentDetails(
                            0, 0, '', '', 0, '', '', False, 0, 0, 0)
                        # seeeders. we get the TD that holds both seeds and leech numbers
                        seedleech = torrent.find_all(
                            "td", attrs={'align': 'center'})
                        if seedleech is None:
                            log.debug('Error getting seed/leech data')

                        seedata = seedleech[2].find(
                            "span", attrs={'class': 'badge badge-success'})
                        if seedata is None:
                            log.debug('Error getting quantity of seeds')
                        torrentdata.seeders = (seedata.text.strip())

                        # leechers. We get the color marked in red, the leechers count
                        leechdata = seedleech[2].find(
                            "span", attrs={'class': 'badge badge-danger'})
                        if leechdata is None:
                            log.debug('Error getting leeches data')
                        torrentdata.leechers = (leechdata.text.strip())

                        # torrent html page link. Gets the second link on the torrent tr and its address
                        link = torrent.find_all('a')[1]['href']
                        if link is None:
                            log.debug("Error getting the torrent permalink")
                        torrentdata.permalink = link

                        # .torrent download link
                        downlink = torrent.find(
                            'a', attrs={'class': 'btn btn-default btn-xs'})['href']
                        if downlink is None:
                            log.debug("Error getting torrent download link")
                        torrentdata.downlink = downlink

                        # Torrent ID . Gets the number on the URL address that is
                        # used to download the torrent file.
                        regx = '.*?\\d+.*?(\\d+)'
                        rg = re.compile(regx, re.IGNORECASE | re.DOTALL)
                        m = rg.search(link)
                        torrentdata.torrentid = (
                            int(m.group(1)) if m else None)

                        # torrentname
                        namedata = torrent.find('span')
                        torrentdata.torrentname = namedata.text.strip()
                        if namedata is None:
                            log.debug('Error getting torrent name')

                        # FileSize
                        sizedata = torrent.find_all("td", {"align": "center"})
                        sizefile = (sizedata[1].text).replace(
                            "(", "").replace(")", "").strip()
                        if sizedata is None:
                            log.debug('Error getting torrent size')
                        torrentdata.filesize = sizefile

                        # FreeLeech. They are marked as "Livre" on the torrent name
                        freeleechdata = torrent.find("font", {"color": "blue"})
                        if freeleechdata is None:
                            torrentdata.freeleech = False
                        else:
                            torrentdata.freeleech = True

                        # TorrentScore is used by couchpotato to decide which file to download
                        # The lines below forces the system to favor the freelech torrents
                        torrscore = 0
                        if torrentdata.freeleech is False:
                            torrscore += tryInt(self.conf('extrascore_freelech'))
                        torrentdata.torrentscore = torrscore

                        # Checks for duplicate torrents found in search and ignores them
                        if torrentlist is not None:
                            torrentAlreadyAdded = False
                            for torrentItem in torrentlist:
                                if torrentItem.torrentid == torrentdata.torrentid:
                                    torrentAlreadyAdded = True
                            if torrentAlreadyAdded is not True:
                                torrentlist.append(torrentdata)
                except:
                    log.error('Failed getting results from %s: %s',
                              (self.getName(), traceback.format_exc()))

            continue

    def getLoginParams(self):
        return {
            'password': str(self.conf('password')),
            'username': str(self.conf('username')),
            'dados': str('ok'),
        }

    def loginSuccess(self, output):
        #Checks if we have loggen in successfully
        return log.debug('Checking login success for Manicomio-share: %s' % ('True' if ('deslogar.php' in output.lower()
                                                                                        or '<title>:: Manicomio Share - A comunidade do Brasil ::</title>' in output.lower()) else 'False'))

    def replaceTitleAndValidateTorrent(self, movie, torrentName):
        # Removes Various tags from the torrent name
        torrentNameCleared = re.sub('\[DualAudio.+?].+[-+]\]', "", torrentName)
        torrentNameCleared = re.sub('\[livre\]', "", torrentNameCleared)
        torrentNameCleared = re.sub('\[Repack\]', "", torrentNameCleared)
        torrentNameCleared = re.sub('Dublado', "", torrentNameCleared)
        # Removes double spacing
        torrentNameCleared = re.sub('  ', "", torrentNameCleared)
        # remove anything between []
        torrentNameCleared = re.sub('\[.[^[]*\]', "", torrentNameCleared)
        torrentNameCleared = re.sub(
            r"^(.*?)\s-\s(?!\d)", "", torrentNameCleared)

        # Couchpotato expects that the movie release year appears next to the torrent name
        torrentNameCleared = torrentNameCleared.replace(
            "[", "(" + str(movie['info']['year']) + ") [")
        # #edge case: some torrent names don't have any brackets so we need to verify if we need to add the year if it's not already there
        hasDateAlready = re.search('\(\d\d\d\d\)', torrentNameCleared)
        if not hasDateAlready:
            torrentNameCleared = torrentNameCleared + \
                " (" + str(movie['info']['year']) + ")"

        return torrentNameCleared

    def login(self):
        output = ""
        # Check if we are still logged in every hour
        now = time.time()
        if self.last_login_check and self.last_login_check < (now - 3600):
            try:
                output = self.urlopen(self.urls['login_check'])
                if self.loginCheckSuccess(output):
                    self.last_login_check = now
                    return True
            except:
                pass
            self.last_login_check = None

        if self.last_login_check:
            return True

        try:
            # Open the login page to load cloudflare cookies.
            output = self.urlopen(self.urls['login'])
            # Now try to login with provided data
            output = self.urlopen(
                self.urls['login'], data=self.getLoginParams())
            # Try to reload the page to see if we have been redirected
            output = self.urlopen(self.urls['login'])
            if self.loginCheckSuccess(output):
                self.last_login_check = now
                self.login_failures = 0
                return True
            error = 'Failed to login'
        except Exception as e:
            if isinstance(e, HTTPError):
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    self.login_failures += 1
                    if self.login_failures >= 3:
                        self.disableAccount()
            error = traceback.format_exc()

        self.last_login_check = None

        if self.login_fail_msg and self.login_fail_msg in output:
            error = "Login credentials rejected."
            self.disableAccount()

        log.error('Failed to login %s: %s', (self.getName(), error))
        return False