Running the app without Installing
==============================

    virutalenv <virtual env directory>
    source <virtual env directory>/bin/activate
    pip install -r requirements.txt
    cd <project directory>
    foreman start

 The above steps will do the following 2 things:
 - start up the web server
 - start the scheduler, with a job running at 22:30 every day for crawling the job sites.

Accessing the app
-----------------
    
    http://0.0.0.0:<PORT_SHOWN_IN_CONSOLE, 5000>

Installing the app as command line tool
=======================================
	
	python setup.py install # this will install zjobs as a command line app

  Setuping the Environemnt Config
  ---------------------------------

    export DB_HOST=<Your db host. default:localhost> 
    export DATABASE=<Your db sid. default:zjobs>
    export DB_USER=<Your db User. default: zjobs>
    export DB_PASSWORD=<Your db password. default:zjobs>

   Using the app
   -------------

	zjobs  # this will start the web application and start the backend scheduler

   Accessing the app
   -----------------
    
    http://0.0.0.0:<PORT_SHOWN_IN_CONSOLE, 5000>