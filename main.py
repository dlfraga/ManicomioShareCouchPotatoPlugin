# coding: utf8
#This code is not endorsed nor approved by the site maintainers or any representatives.
#Use at your own risk.
#The plugin was based on the work of https://github.com/flightlevel/TehConnectionCouchPotatoPlugin/ and
#https://github.com/djoole/couchpotato.provider.t411
#most credits goes to them
from bs4 import BeautifulSoup

from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from requests import HTTPError
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider

import traceback
import re
import time
log = CPLog(__name__)

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
    #'search': 'http://www.manicomio-share.com/busca-filmes.php?vince=0&onde=1&search=%s&parent_categ=0&qualite=&cor=&codecvideo=&extensao=&tipoaudio=&lang=0&paisorigem=&direc=',
    urls = {
        'baseurl': 'https://www.manicomio-share.com/',
        'login': 'https://www.manicomio-share.com/',
        'login_check': 'https://www.manicomio-share.com/deslogar.php',        
        'search': 'https://www.manicomio-share.com/pesquisa.php?busca=%s&cat=%s&opt2=0&vnc=0&ano=0&opt=0',
        'torrentdetails': 'https://www.manicomio-share.com/ajax/ajax2.php?torrent=%s',
        'imdbreleaseinfo': 'http://www.imdb.com/title/%s/releaseinfo'
    }
        

    http_time_between_calls = 5  # seconds
    
    cat_ids = [
                    ([127], ['720p', '1080p','brrip']),
                    ([147,141],['3d']),
                    ([189],['4K','2160p']),
                    ([132,183,143],['bdrip']),
                    ([142], ['bd25','bd50']),                    
                    ([34,144], ['dvdrip','dvdr']),
                    ]

    def _searchOnTitle(self, title, movie, quality, results):  
        if self.conf('only_freeleech'):
                onlyfreeleech = True
        else:
                onlyfreeleech = False        
            
        if not '/deslogar.php' in self.urlopen(self.urls['login'], data=self.getLoginParams()).lower():
            log.info('problems logging into manicomio-share.com')
            return []                        
        torrentlist = []            
        log.info('Looking on manicomio-share for movie named %s, with quality %s and category code %s' % (title, str(quality['custom']['quality']), self.getCatId(quality)))
        
        for categoryCode in self.getCatId(quality):
            data = self.getHTMLData(self.urls['search'] % (tryUrlencode(title) , categoryCode))                                    
            if data:
                try:
                    resultstable = BeautifulSoup(data).find('table', attrs={'id': 'tbltorrent'})
                    if resultstable is None:
                        log.info('movie not found on Manicomio-share. Maybe try an alternative name?')
                        return []
    
                    htmltorrentlist = resultstable.find_all('tr', attrs={'id': 'closest'})                
                    for torrent in htmltorrentlist:
                        torrentdata = TorrentDetails(0, 0, '', '', 0, '', '', False, 0, 0, 0)
    
                        # seeeders. we get the first span tag that holds both seeds and leech numbers
    #                     log.debug(torrent)
                        seedleech = torrent.find_all("span", attrs={'class': 'h3o'})
                        seedata = seedleech[0].find("font", attrs={'color': 'green'})
                        torrentdata.seeders = (seedata.text.strip())
    
                        # leechers. We get the color marked in red, the leechers count
                        leechdata = seedleech[1].find("font", attrs={'color': 'red'})
                        torrentdata.leechers = (leechdata.text.strip())
    
                        # torrent html page link. Gets the second link on the torrent tr and its address
                        link = torrent.find_all('a')[1]['href']
                        torrentdata.permalink = link
    
                        # .torrent download link
                        downlink = torrent.find('a', attrs={'class': 'btn btn-default btn-xs'})['href']
                        torrentdata.downlink = downlink
    
                        # Torrent ID . Gets the number on the URL address that is
                        # used to download the torrent file.
                        regx = '.*?\\d+.*?(\\d+)'
                        rg = re.compile(regx, re.IGNORECASE | re.DOTALL)
                        m = rg.search(link)
                        torrentdata.torrentid = (int(m.group(1)) if m else None)
    
                        # torrentname
                        namedata = torrent.find('span')
                        torrentdata.torrentname = namedata.text.strip()
                        
                        #movie year. we also do a comparation to see if the torrent we've found is really the one we want
                        #we do that using the movie release year
                        movieYear = torrent.find('font', attrs={'color': 'green'}).text.strip()
                        if movieYear != (str(movie['info']['year'])):
                            log.debug("Wrong movie date, found " + movieYear + " Expected: " + str(movie['info']['year']) )
                            continue
                        
                        # FileSize
                        sizedata = torrent.find_all("span", {"class": "h3t"})
                        sizefile = (sizedata[1].text).replace("(", "").replace(")", "").strip()
                        torrentdata.filesize = sizefile
                        
                        # FreeLeech. They are marked as "Livre" on the torrent name
                        freeleechdata = torrent.find("font", {"color": "blue"})
                        if freeleechdata is None:
                            torrentdata.freeleech = False
                        else:
                            torrentdata.freeleech = True
    
                        # TorrentScore
                        torrscore = 0
                        if torrentdata.freeleech is False:                        
                            torrscore += tryInt(self.conf('extrascore_freelech'))                        
                        torrentdata.torrentscore = torrscore
    
                        # datetorrentadded
#                         try:
                            # we need to get another page that returns the torrent details
                            # http://www.manicomio-share.com/ajax/ajax2.php?torrent=ID 
                        log.debug('Torrent found: ' + torrentdata.torrentname)                   
                        # Test if the Freelech box has been checked
                        if (onlyfreeleech is False) or (onlyfreeleech is True and torrentdata.freeleech is True):
                            # Only Freelech is switched off OR only Freelech is ON and the torrent is a freeleech,
                            # so safe to add to results
                                  
                            torrentlist.append(torrentdata)
    
                    log.info('Number of torrents found from manicomio-share = ' + str(len(torrentlist)))
    
                    for torrentfind in torrentlist:                    
                        log.info('manicomio-share found ' + torrentfind.torrentname)    
#                        log.debug(self.replaceTitleAndValidateTorrent(movie, title, torrentfind.torrentname))                              
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
    
                except:
                    log.error('Failed getting results from %s: %s',
                              (self.getName(), traceback.format_exc()))
                    
    def getLoginParams(self):        
        log.debug('Getting login params for Manicomio-share ')            
        return {
            'password': str(self.conf('password')),
            'username': str(self.conf('username')),
            'dados': str('ok'),
        }

    def loginSuccess(self, output):
        #log.debug('Debug login: ' + output)    
        #log.debug('Checking login success for Manicomio-share: %s' % ('True' if ('deslogar.php' in output.lower()
                                                                                 #or '<title>:: Manicomio Share - A comunidade do Brasil ::</title>' in output.lower()) else 'False'))
        return '<title>MS-->Logue-se : :: Manicomio Share - A comunidade do Brasil ::</title>' in output

    loginCheckSuccess = loginSuccess
#     
#     def getBrazillianTitle(self, title, movie):        
#         # This function scrapes the imdb page associated with the movie's release info
#         log.debug('Looking on IMDB for Brazillian title of: ' + title)
#         try:            
#             result = self.getHTMLData(self.urls['imdbreleaseinfo'] % tryUrlencode(movie['identifiers']['imdb']))         
#             if result is None: 
#                 log.debug('IMDB could not find a movie corresponding to : ' + title)
#                 return None
#             else:
#                 try:
#                     akasoup = BeautifulSoup(result, ''html.parser') 
#                     akatable = akasoup.find('table', attrs={'id': 'akas'})    
#                     pattern = re.compile(r'^(Brazil)$')
#                     return akatable.find('td', text=pattern).parent.find_all()[1].text
#                 except Exception:
#                     log.debug("Movie doesn't have a translated name or is in native language")
#                     return title
#         except:
#             log.error('Failed to parse IMDB page: %s' % (traceback.format_exc()))
            
    def replaceTitleAndValidateTorrent(self, movie, torrentName):
        #Removes [DualAudio *] tags and subtitle tags [-] or [+]
        torrentNameCleared = re.sub('\[DualAudio.+?].+[-+]\]',"", torrentName)
        torrentNameCleared = re.sub('\[livre\]', "", torrentNameCleared)
        torrentNameCleared = re.sub('\[Repack\]', "", torrentNameCleared)
        torrentNameCleared = re.sub('Dublado', "", torrentNameCleared)
        torrentNameCleared = re.sub(r"^(.*?)\s-\s(?!\d)","",torrentNameCleared)
        #originalTitle = movie['title']
        #originalTitle = originalTitle.replace(":","")
        #originalTitle = originalTitle.replace("-","")
        #torrentNameCleared = torrentNameCleared.replace(translatedName, movie['title'])
            
        #Couchpotato expects that the movie release year appears on the torrent name
        torrentNameCleared = torrentNameCleared.replace("[", "(" + str(movie['info']['year']) + ") [")
        ##edge case: some torrent names don't have any brackets so we need to verify if we need to add the year if it's not already there
        hasDateAlready = re.search('\(\d\d\d\d\)', torrentNameCleared)
        if not hasDateAlready:
            torrentNameCleared = torrentNameCleared + " (" + str(movie['info']['year']) + ")"
                        
        return torrentNameCleared
    
    def login(self):
        # Check if we are still logged in every hour
        now = time.time()
        if self.last_login_check and self.last_login_check < (now - 3600):
            try:
                output = self.urlopen(self.urls['login_check'])
                if self.loginCheckSuccess(output):
                    self.last_login_check = now
                    return True
            except: pass
            self.last_login_check = None

        if self.last_login_check:
            return True

        try:
            #Open the login page to load cloudflare cookies. 
            output = self.urlopen(self.urls['login'])
            #log.debug('Debug ------ 1: ' + output)    
            #Now try to login with provided data
            output = self.urlopen(self.urls['login'], data = self.getLoginParams())           
            #log.debug('Debug login --------2: ' + output)    

            if self.loginSuccess(output):
                self.last_login_check = now
                self.login_failures = 0
                return True

            error = 'unknown'
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
