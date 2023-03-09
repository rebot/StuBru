# Studio Brussel | Last.fm Scrobbler

> UPDATE: Code adapted to run on Github Actions - README Should be updated as well (WIP)

Een tweetal jaar terug bezorgde ik [Last.fm] van een [Studio Brussel](https://www.last.fm/user/Studio-Brussel) pagina waarop heden meer dan 275 000 tracks werden gescrobbled. Op aanvraag maak ik nu een gelijkaardige pagina voor `Bruut`, de harde gitaren muziek stream van Studio Brussel. 

## Open Source en Freeware

Belangrijk vind ik dat dergelijke kleine projecten kostenloos moeten kunnen. Het project steunt op het werk van andere. Zo maak ik gebruik van [pylast], een Python interface gebouwd rond de [Last.fm](https://last.fm) API. 

# Bouw je eigen Scrobbler!

Het resultaat kun je hier terugvinden:

| Radio Stream        | Spotify Playlist        | Icecast        |
| ------------------- |------------------------ | -------------- |
| [StuBru - Bruut]    | [StuBru ｜ Bruut]       | [Bruut]        |
| [StuBru - Hooray]   | [StuBru ｜ Hooray]      | [Hooray]       |
| [StuBru - Tijdloze] | [StuBru ｜ Tijdloze]    | [De Tijdloze]  |

## Scrobble audio Stream
De streams worden gehost met een [icecast] server dat overigens open source is. Een overzicht van alle toegankelijke streams vind je op de statuspagina van de server: [http://icecast.vrtcdn.be/status-json.xsl](http://icecast.vrtcdn.be/status-json.xsl). Ik raad je aan deze pagina te openen in Firefox. Firefox herkent dat dit `JSON` is en geeft dit dan ook grafisch mooi weer. 

De `listenurl` van het radiostation dat je wil scrobblen vind je terug op de statuspagina. De domeinnaam `localhost:80` en poortnummer verander je door `icecast.vrtcdn.be`. Als je nu een `GET` verzoek stuurt met als header `Icy-MetaData = 1` naar de `listenurl`, dan krijg je stream terug met als bijkomende *payload* wat *meta data* van de stream, waaronder een `StreamTitle=<titel>`. Er zijn een aantal *bits* gereserveerd voor de *meta data*, maar ik vond geen bijkomende informatie over het formaat. Een eenvoudige *regular expression* ([regex]) op de gedecodeerde data (aanname encoding `utf-8`) leek al te volstaan om de titel te achterhalen. Tot op heden had ik geen *encoding* issues, maar mogelijks is de data niet *unicode* encoded. 

### Bottom line 

De statuspagina bevat ook de artiest en het nummer dat, op het moment dat je ze bevraagde, wordt afgespeeld. Het is dus niet nodig om de *radio stream* te inspecteren. Met behulp van `JSON Path` haal ik de titel uit de statuspagina, dit voor verschillende *radio streams*. Erna splits ik de titel op in de auteur en titel en zoek ik het bijhorende liedje in de database van [Last.fm] met behulp van [pylast]. Het nummer scrobble ik naar [Last.fm] als de naam van het nummer **niet** overeen stemt met het laatst afgespeelde nummer. Elke 2 minuten wordt de status pagina opnieuw bevraagd en wordt het script opnieuw uitgevoerd.

## Spotify afspeellijst

[Last.fm] houdt voortaan alle afgespeelde nummer bij. Met deze gegevens kunnen we nieuwe toepassingen bedenken. Als *proof of concept* [POC](https://en.wikipedia.org/wiki/Proof_of_concept) bouwde ik een script dat de top 10 van de meest afgespeelde nummers bijhoudt in een Spotify afspeellijst. Hiervoor maak ik gebruik van [spotipy]. Elke 24u (om 8u 's morgens) wordt de lijst herwerkt. Het eerste nummer in de afspeellijst is het meest afgespeelde nummer.   

[icecast]: https://icecast.org/ 
[Last.fm]: https://www.last.fm/
[pylast]: https://github.com/pylast/pylast
[spotipy]: https://spotipy.readthedocs.io/en/latest/
[regex]: https://blog.usejournal.com/regular-expressions-a-complete-beginners-tutorial-c7327b9fd8eb
[Bruut]: https://radioplus.be/#/bruut/playlist
[Hooray]: https://radioplus.be/#/hooray/playlist
[De Tijdloze]: https://radioplus.be/#/de-tijdloze/playlist
[StuBru - Bruut]: https://www.last.fm/user/StuBru-Bruut
[StuBru - Hooray]: https://www.last.fm/user/StuBru-Hooray
[StuBru - Tijdloze]: https://www.last.fm/user/StuBru-Tijdloze
[StuBru ｜ Bruut]: https://open.spotify.com/playlist/0IAaRXVmeQWwBDGxasqX90?si=WsejBqOkQVijpieeeo3V4A
[StuBru ｜ Hooray]: https://open.spotify.com/playlist/6Z7MpfeMUcOte4hMJzzoGu?si=c_3EyI3GQ12rKW3zwhH9xg
[StuBru ｜ Tijdloze]: https://open.spotify.com/playlist/2evppk4paQV6TXcLRvnnLY?si=8fhZ_ZBQQOSzrCvXd_5e3g