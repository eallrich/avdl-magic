avdl-magic
==========
A perhaps not-so-magical audio/video download assistant.

Purpose
-------
Exposes some of the power of youtube-dl in a simple web UI with the intent that
it enable a casual end user to easily retrieve the audio from a Youtube video
as an .mp3 file.

Deploying to Heroku
-------------------
The easiest deployment option is through Heroku using the Redistogo addon. To
follow these steps, you'll need the [Heroku Toolbelt](https://toolbelt.heroku.com/)
installed.

```shell
$ git clone https://github.com/eallrich/avdl-magic.git
$ cd avdl-magic
$ heroku create
# The free 5MB plan will be sufficient for our purposes
$ heroku addons:create redistogo:nano
# This 'git push' will take a while due to the included ffmpeg binary blobs
$ git push heroku master
$ heroku open
```

Acknowledgements
----------------
This project builds upon the magic acts already performed by these giants:
+ [AngularJS](https://angularjs.org/)
+ [Bootstrap](http://getbootstrap.com/)
+ [FFmpeg](https://www.ffmpeg.org/) via [John Van Sickle's FFmpeg Builds](http://johnvansickle.com/ffmpeg/)
+ [Flask](http://flask.pocoo.org/)
+ [Redis](http://redis.io/)
+ [Requests](http://docs.python-requests.org/)
+ [RQ](http://python-rq.org/)
+ [youtube-dl](https://rg3.github.io/youtube-dl/)
+ And many more, too!
