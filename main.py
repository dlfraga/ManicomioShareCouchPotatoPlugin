# coding: utf8
#This code is not endorsed nor approved by the site maintainers or any representatives.
#Use at your own risk.
#The plugin was based on the work of https://github.com/flightlevel/TehConnectionCouchPotatoPlugin/ and
#https://github.com/djoole/couchpotato.provider.t411
#most credits goes to them
from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode, toUnicode
from couchpotato.core.helpers.variable import tryInt, getIdentifier
from couchpotato.core.logger import CPLog
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
        'baseurl': 'http://www.manicomio-share.com/',
        'login': 'http://www.manicomio-share.com/',
        'login_check': 'http://www.manicomio-share.com/mailbox.php?Entrada',        
        'search': 'http://www.manicomio-share.com/busca-filmes.php?&search=%s',
        'torrentdetails': 'http://www.manicomio-share.com/ajax/ajax2.php?torrent=%s',
        'imdbreleaseinfo': 'http://www.imdb.com/title/%s/releaseinfo'
    }

    http_time_between_calls = 2  # seconds

    def _searchOnTitle(self, title, movie, quality, results):                
        if self.conf('only_freeleech'):
                onlyfreeleech = True
        else:
                onlyfreeleech = False        
            
        if not '/deslogar.php' in self.urlopen(self.urls['login'], data=self.getLoginParams()).lower():
            log.info('problems logging into manicomio-share.com')
            return []                        
        torrentlist = []
            
        translatedMovieTitle = self.getBrazillianTitle(title, movie)
        originalMovieTitle = title
        titleToBeSearched = title
        if isinstance(originalMovieTitle, str):
            titleToBeSearched = originalMovieTitle.encode('latin1')
        if translatedMovieTitle is not None:            
            titleToBeSearched = translatedMovieTitle.encode('latin1')

        log.debug('Looking on manicomio-share for movie named %s' % (originalMovieTitle))                             
            
        data = self.getHTMLData(self.urls['search'] % tryUrlencode(originalMovieTitle))        
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
                    try:
                        # we need to get another page that returns the torrent details
                        # http://www.manicomio-share.com/ajax/ajax2.php?torrent=ID
                        data = self.getHTMLData(self.urls['torrentdetails'] % tryUrlencode(torrentdata.torrentid))
                        # Hack to avoid needing to load a specific locale on the system
                        # this was done due to some python distributions that are used on NAS
                        # systems that doesn't have all locales installed
                        monthofyear = {
                            'Janeiro': '1',
                            'Fevereiro': '2',
                            'Marco': '3',
                            'Abril': '4',
                            'Maio': '5',
                            'Junho': '6',
                            'Julho': '7',
                            'Agosto': '8',
                            'Setembro': '9',
                            'Outubro': '10',
                            'Novembro': '11',
                            'Dezembro': '12'
                        }                        
                        soup = BeautifulSoup(data, "lxml")
                        body = soup.find('body')
                        datestr = body.text.split(",")[1]
                        # example string:  06 de Outubro de 2015 \u00e0s 17:31"                        
                        datestr = re.sub('\\\\u00e0s\ ', '', datestr)
#                         recom = re.compile(u'\u00e7\', re.UNICODE)                        
                        datestr = re.sub('\\\\u00e7', 'c', datestr)
                        datestr = re.sub('"', '', datestr)                        
                        monthinportuguese = datestr.split(" ")[3]
                        datechanged = re.sub(monthinportuguese, monthofyear[
                                             monthinportuguese], datestr)
                        datechanged = datechanged.strip()
                        # after 'conversion': 06 de 10 de 2015 17:31
                        addeddatetuple = time.strptime(datechanged, '%d de %m de %Y %H:%M')
                        torrentdata.datetorrentadded = int(time.mktime(addeddatetuple))
                    except:
                        log.error('Unable to convert datetime from %s: %s',
                                  (self.getName(), traceback.format_exc()))
                        torrentdata.datetorrentadded = 0

                    # ageindays
                    torrentdata.ageindays = int(
                        (time.time() - torrentdata.datetorrentadded) / 24 / 60 / 60)

                    # Test if the Freelech box has been checked
                    if (onlyfreeleech is False) or (onlyfreeleech is True and torrentdata.freeleech is True):
                        # Only Freelech is switched off OR only Freelech is ON and the torrent is a freeleech,
                        # so safe to add to results
                              
                        torrentlist.append(torrentdata)

                log.info('Number of torrents found from manicomio-share = ' + str(len(torrentlist)))

                for torrentfind in torrentlist:                    
                    log.info('manicomio-share found ' + torrentfind.torrentname)                                  
                    results.append({
                        'leechers': torrentfind.leechers,
                        'seeders': torrentfind.seeders,
                        'name': self.replaceTitleAndValidateTorrent(movie, translatedMovieTitle, torrentfind.torrentname),
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
        log.debug('Checking login success for Manicomio-share: %s' % ('True' if ('deslogar.php' in output.lower()
                                                                                 or '<title>:: Manicomio Share - A comunidade do Brasil ::</title>' in output.lower()) else 'False'))
        return 'deslogar.php' in output.lower() or ':: Manicomio Share - A comunidade do Brasil ::' in output.lower()

    loginCheckSuccess = loginSuccess
    
    def getBrazillianTitle(self, title, movie):
        # This function scrapes the imdb page associated with the movie's release info
        log.debug('Looking on IMDB for Brazillian title of: ' + title)
        try:            
            result = self.getHTMLData(self.urls['imdbreleaseinfo'] % tryUrlencode(movie['identifiers']['imdb']))         
            if result is None: 
                log.debug('IMDB could not find a movie corresponding to : ' + title)
                return None
            else:
                try:
                    akasoup = BeautifulSoup(result, 'lxml') 
                    akatable = akasoup.find('table', attrs={'id': 'akas'})    
                    pattern = re.compile(r'^(Brazil)$')
                    return akatable.find('td', text=pattern).parent.find_all()[1].text
                except Exception:
                    log.debug("Movie doesn't have a translated name or is in native language")
                    return title
        except:
            log.error('Failed to parse IMDB page: %s' % (traceback.format_exc()))
            
    def replaceTitleAndValidateTorrent(self, movie, translatedName, torrentName):        
        #Removes [DualAudio *] tags and subtitle tags [-] or [+]
        torrentNameCleared = re.sub('\[DualAudio.+?].+[-+]\]',"", torrentName)
        torrentNameCleared = re.sub('\[livre\]', "", torrentNameCleared)
        torrentNameCleared = re.sub('\[Repack\]', "", torrentNameCleared)
        torrentNameCleared = re.sub('Dublado', "", torrentNameCleared)
        torrentNames = torrentNameCleared.split("-")
        try:
            torrentNameCleared = torrentNames[1]
        except Exception:
            pass
        
        originalTitle = movie['title']
        originalTitle = originalTitle.replace(":","")
        originalTitle = originalTitle.replace("-","")
        torrentNameCleared = torrentNameCleared.replace(originalTitle, movie['title'])    
        torrentNameCleared = torrentNameCleared.replace("[", "(" + str(movie['info']['year']) + ") [")        
        log.debug("Nome limpo: " + torrentNameCleared + " Nome renomeado: " + movie['title'])        
        return torrentNameCleared
