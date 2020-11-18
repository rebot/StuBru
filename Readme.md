# Bruut | Studio Brussel

Een tweetal jaar terug bezorgde ik [Last.fm](https://www.last.fm/user/Studio-Brussel) van een [Studio Brussel](https://www.last.fm/user/Studio-Brussel) pagina waarop heden meer dan 275 000 tracks werden gescrobbled. Op aanvraag maak ik nu een gelijkaardige pagina voor `Bruut`, de harde gitaren muziek stream van Studio Brussel. 

## Open Source en Freeware

Belangrijk vind ik dat dergelijke kleine projecten kostenloos moeten kunnen. Het project steunt op het werk van andere. Zo maak ik gebruik van [pylast](https://github.com/pylast/pylast), een Python interface gebouwd rond de [Last.fm](https://last.fm) API. 

## Bouw je eigen Scrobbler!
### Studio Brussel Audio Stream
De streams worden gehost met een [icecast] server dat overigens open source is. Een overzicht van alle toegankelijke streams vind je op de statuspagina van de server: [http://icecast.vrtcdn.be/status-json.xsl](http://icecast.vrtcdn.be/status-json.xsl). Ik raad je aan deze pagina te openen in Firefox. Firefox herkent dat dit `JSON` is en geeft dit dan ook grafisch mooi weer. 

TODO
- Toevoegen handleiding python omgeving
- Toevoegen configuratie met Heroku

## Disclaimer

Hmmm... 

[icecast]: https://icecast.org/