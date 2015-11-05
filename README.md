# ManicomioShareCouchPotatoPlugin
Plugin for couchpotato to search manicomio-share for files. 
To install, clone the repo to your custom_plugins folder and after restarting couchpotato enable it in the settings.


## Know problems

1.  Some brazillian titles are not found by couchpotato due to the search looking for non latin file names.
2.  If the release is larger than couchpotato expects it will not download the file.
3.	The code only searches for native media names, not the localized versions, although the method for translation is already implemented.
4.	Various methods of validation were implemented, but results may vary.
3.	Expect the unexpected: This code was created by a complete beginner. Post an issue if you have problems.

**Disclaimer**
This code is not endorsed nor approved by the site maintainers or any representatives.
Use at your own risk.
The plugin was based on the work of https://github.com/flightlevel/TehConnectionCouchPotatoPlugin/ and https://github.com/djoole/couchpotato.provider.t411 . Most credits goes to them. 
