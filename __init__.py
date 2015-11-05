#This code is not endorsed nor approved by the site maintainers or any representatives.
#Use at your own risk.
#The plugin was based on the work of https://github.com/flightlevel/TehConnectionCouchPotatoPlugin/ and
#https://github.com/djoole/couchpotato.provider.t411
#most credits goes to them
from .main import ManicomioShare


def autoload():
    return ManicomioShare()


config = [{
              'name': 'manicomioshare',
              'groups': [
                  {
                      'tab': 'searcher',
                      'list': 'torrent_providers',
                      'name': 'Manicomio-share',
                      'description': '<a href="http://www.manicomio-share.com/">Manicomio-Share</a>',
                      'wizard': True,
                      'icon': 'AAABAAEAEBAAAAAAAABoBQAAFgAAACgAAAAQAAAAIAAAAAEACAAAAAAAAAEAAAAAAAAAAAAAAAEAAAAAAAAAAAAAKJ9EACtuOQAGDWUAoMCjAI6MvADV0dQAMXA/AJmfpAC2srgAKZhCABaDMQBHn18AGlApANDQ0gAgSikACTwSACCDOgCzYkAAusi7AAs+GAA3oUsAHJo3AH1/qQAQeCwA2tfVAKCdlgDw6+wAEU4bABN7NQBepXEAx2lDAChkOADSZjoAK6FDAMBUKQDBxMIADnoqAB2v2AB6n4MAw8rCACBhMADTYh0AEHwwAMTLxQDc2dwAmJe7AGOicgDf4twAS5ZhAMG3rgDK0tEALmI8ACpoPAAjSSgA19nUAFlnXABYrL0ADRoJAMXPwADAjnQALq7fAHCJggDOzs8AGYk0ABBoGgAUp9QAHYQ3AMJYLgDT0tIAzdvSALZgRgCTPBIAgJWCAB2aOgDCOxcAI1gyALhNFwDJx8QAxszKAGWXdwARB40AzMjHABGHLwCpNRgAyc/KAA1eIQAkbTsApqelAM7QzQBNm2AAH3s4AEJ8VQDeazEAprSoAOjn7QAfhqkAyZiTAHmchgAORhkAw8fFAN3l3wDhXyAAys/LAIWWoQDM0M4AF1srAB1UKAAhhjYAoqbHACUgCwA8klAAHpM5ACMlcwCqtawAE2uQAA92KwAQdC4AmjIjALGzrwA5mccAIpg/AA6IKwBgoXMAYJ92ABWBMQATijEAzc7JAOne5gDN3M8A5+fmADaaTgAzaEAAo76kALrCygDgbDYA1tbYABJ6LwAZPxgA8fDvAPbt7wDPyc0A4uLhABSQMgATlywAHaDMAKimrgDl5uQALG0+AJm3vQCftL0A7uPkANfW0AAWORkAHWEtACMaigDZ2NYAwohwABN9MADaurMAx8rIABOAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEtSMAAwaSQsjgAAAAAAgqB2WFQEdYmeK3ReAAAAAJkccgk4bh0LelN9JWUAAACcF3EyczoYjSePfqEGAABfmy6VlkhOVZBKFnBDgAAAA1GSOZ8+gWwKIgF5hQAAAG0FkU9NFFlvgxVbO4gAAAAAMyaGnWOYMVoMSUARMAAAAAhCaDwQf2p7Hi98UDAAAAB4PRoqZEyTEylXXGcAAAAAl2A/ZkWKmg4wMDAwAAAAAAAAG10SHzZWQWJ3DWsZAAAAAIxHh0QALQ8HlAI1IDcAAACLYSEjAAAAADCENCgAAAAAAAAAAAAAAAAARgAAAP//AADiDwAAgAcAAIADAACAAwAAAAMAAAAHAAAABwAAgAMAAIADAACABwAAgAcAAOABAADhAAAA4eEAAP/3AAA=',
                      'options': [
                          {
                              'name': 'enabled',
                              'type': 'enabler',
                              'default': False,
                          },
                          {
                              'name': 'username',
                              'default': '',
                          },
                          {
                              'name': 'password',
                              'default': '',
                              'type': 'password',
                          },
                          {
                              'name': 'seed_ratio',
                              'label': 'Seed ratio',
                              'type': 'float',
                              'default': 2,
                              'description': 'Will not be (re)moved until this seed ratio is met.',
                          },
                          {
                              'name': 'seed_time',
                              'label': 'Seed time',
                              'type': 'int',
                              'default': 96,
                              'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                          },                          
                          {
                              'name': 'extrascore_freelech',
                              'advanced': True,
                              'label': 'Freeleech Extra',
                              'type': 'int',
                              'default': 20,
                              'description': 'Favours [FreeLeech / livre] releases by giving them extra score eg.1000'
                          },                          
                          {
                              'name': 'only_freeleech',
                              'label': 'Freeleech Only',
                              'default': False,
                              'type': 'bool',
                              'description': 'Only search for [FreeLeech / livre] torrents.',
                          },
                          {
                              'name': 'extra_score',
                              'advanced': True,
                              'label': 'Extra Score',
                              'type': 'int',
                              'default': 20,
                              'description': 'Starting score for releases found from ManicomioShare.',
                          }
                      ],
                  },
              ],
          }]
