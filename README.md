avdl-magic
==========
A perhaps not-so-magical audio/video download assistant.

![Screenshot of a fresh instance](/docs/fresh.jpg?raw=true "A freshly loaded instance")

Purpose
-------
Exposes some of the power of youtube-dl in a simple web UI with the intent that
it enable a casual end user to easily retrieve the audio from a YouTube video
as an .mp3 file.

Heads-up! Copyright infringement is serious business and can come with legal
consequences. This program comes with ABSOLUTELY NO WARRANTY; for details
see [the license](/LICENSE). Please use this software responsibly.

Deploying to Heroku
-------------------
[![Deploy to Heroku button](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/eallrich/avdl-magic)

The easiest deployment option is through Heroku using the 'click to deploy'
button, above. It will automate the steps below. You can also follow along with
these commands if you would prefer to deploy manually. You'll just need to have
the [Heroku Toolbelt](https://toolbelt.heroku.com/) installed.

```shell
$ git clone https://github.com/eallrich/avdl-magic.git
$ cd avdl-magic
$ heroku create
# The free 25MB plan will be more than sufficient for our purposes
$ heroku addons:create heroku-redis:hobby-dev
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
