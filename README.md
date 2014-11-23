Running the app
===============

    virutalenv <virtual env directory>
    source <virtual env directory>/bin/activate
    pip install -r requirements.txt
    cd <project directory>
    foreman start

 The above steps will do the following 2 things:
 - start up the web server
 - start the scheduler, with a job running at 22:30 every day for crawling the job sites.

Accessing the app
=================
    
    http://0.0.0.0:<PORT_SHOWN_IN_CONSOLE, 5000>