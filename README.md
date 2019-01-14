# ManicomioShareCouchPotatoPlugin #
Plugin para o couchpotato a fim de pesquisar o manicomio-share por arquivos.
Para instalar, clone o repositório para a sua pasta de custom_plugins e depois de reiniciar o couchpotato habilite o plugin nas configurações.
___
Plugin for couchpotato to search manicomio-share for files. 
To install, clone the repo to your custom_plugins folder and after restarting couchpotato enable it in the settings.

## Problemas conhecidos /  Know problems ##

+ Alguns torrents no tracker tem datas de release errada ou utilizam as datas do release no brasil, enquanto o couchpotato sempre busca pelas datas americanas e isso faz com que o couchpotato ignore os torrents durante a busca. Foi adicionado um hack que faz a pesquisa procurar pelo ano do arquivo + 1 caso a primeira tentativa de busca falhe totalmente
+ Caso um filme não seja encontrado, selecione o nome em portugues no Couchpotato
+ Vários métodos de validação de torrents foram implementados mas os resultados podem variar. Exemplo: Torrents com tamanho de DVD mas classificados no site como 720P são considerados DVD pelo couchpotato, pois é o tamanho que é analisado
___
+ Some torrents in the tracker have wrong release dates or use the brazillian release dates, while couchpotato always looks for american release dates and this results in couchpotato ignoring some torrents during the search. A hack was added to the code that makes the search look for the release date + 1 in case the normal search fails entirely. This was not tested extensively
+ If a movie isn't found, choose the brazillian name on couchpotato
+ Various methods of torrent validation were implemented but results may vary. For example: A Torrent with DVD filesize but marked on the site as 720P sometimes are classified by couchpotato as DVD image, because it always looks at filesizes to determine quality

**Disclaimer** 
Este código não é endossado e nem aprovado pelos mantenedores do site ou qualquer representante.
Use ao seu próprio risco.
O plugin foi criado baseado no trabalho de https://github.com/flightlevel/TehConnectionCouchPotatoPlugin/ e https://github.com/djoole/couchpotato.provider.t411. Maior parte dos créditos vai para eles. 
___
This code is not endorsed nor approved by the site maintainers or any representatives.
Use at your own risk.
The plugin was based on the work of https://github.com/flightlevel/TehConnectionCouchPotatoPlugin/ and https://github.com/djoole/couchpotato.provider.t411 . Most credits goes to them. 

## Desenvolvimento / Development ##

Visual Studio Code
Python 2.7
