-- Update --

This fork has three branches:
 - master: exactly the same as berak's ants-tcp except for this readme
 - asteroids: modified to use the proposed asteroids game
 - wargame: modified to use the (incomplete) risk-like game

A few starter packages for asteroids can be found here:

https://github.com/smiley1983/aichallenge/tree/epsilon/asteroids/dist

An ocaml starter for wargame can be found here:

https://github.com/smiley1983/aichallenge/tree/war/wargame/dist/starter_bots

You can download all three server packages here:

https://github.com/smiley1983/ants-tcp/tags

currently configured like so: 

Ants: ports 2080 and 2081
Asteroids: 6020 and 6021
Wargame: 6030 and 6031



-- Previous readme --

*the contest is over!*

	thank you, accoun, bmh, fluxid, romans01 , and all nameless others, who hosted it,
	fixed it's countless bugs, or generally endured it's various deficiencies..


the running ones i know of:
	http://ants.fluxid.pl    		// fluxid		(DE)
	http://tcpants.com       		// romans01		(US)
	http://ash.webfactional.com/	// ash0d		(US) calif.
	http://213.88.39.97:2080/		// accoun		(RU)
	http://bhickey.net:2080/		// ?? 			(US)
	

most of it is written in python, you'll need version >= 2.6 for this (fractions)
also you'll need php5.3 for the default trueskill impl, or java for the jskills version

you will need to start 
 * tcpserver.py (to run the games), as well as 
 * webserver.py (to show the results to the outer world).

people, who want to play a game here will need to download [your_webserver_url]/clients/tcpclient.py to proxy their bot-io to the tcpserver


feel free to edit/change anything you like, after all, it's YOU, who will be hosting that..
please fork it on github, to make it easy for me and others to pull in any good idea/change you have.


tcpserver.py:
	please look at the options & edit at the bottom in main.
	default port is 2081.
	about the trueskill impl:
		the most stable implementation is the php one. it needs php 5.3, though.
		this is choosen by default, now.
		as a fallback, the previous 'jskills' and 'py' impls are supplied here, too.
			(jskills has problems with draws, thus breaks sometimes)
			(trueskill.py has a bias problem, mu won't rise properly) 
		
webserver.py:
	default port is 2080.
	please look at the options & edit at the bottom in main.
	change the 'host' option to url of your website


sql.py:
	small sql admin shell to peek into the db, extract a replay, 
	reset the rankings, whatever.



problem/todo section:
	fluxid reported/(cursed) a lot of hanging threads, resulting in not freeing socket fds.
	hope that got fixed by adding a proper timeout on the accepted client socks, killing those zombies.
		please send an issue, if you still get this.

	you can't just force people playing constantly here, so the ranking 
	suffers from players playing a few good games and never return,
	fluctuations in the player skills present, and such.
	
	there's no pairing. just first comes, first served.
	
	

the previous PW code:
	https://github.com/McLeopold/TCPServer
	http://www.benzedrine.cx/planetwars/server.tar.gz 
