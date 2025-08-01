<p>
  <img style="margin-top: 20px; margin-bottom: 3px; float: right;" src="https://healthscore.pythonanywhere.com/static/healthscore/images/hero--train.webp" width="200" title="hover text">
</p>

CLF Healthscore Tool
============
Author: *Chris Stolte <chris@deepgreensoft.com>*


Background
----------

The healthscore tool started as a Python command line program, developed by Emily Fang at MIT.
Many of the datasets were identified and incorporated during this initial phase
of the project, and the great majority of the content that appears in the output
spreadsheet was authored by her in cooperation with CLF staff. The
metrics and calculations used have been migrated to this version
almost without changes, save a couple of one-off tweaks here and there.

This project is a web-based version of that tool, and was co-developed by
[Deep Green Software](https://deepgreensoft.com) and
[Tamarack Media Cooperative](https://tamarackmedia.com/). It was created with a few key goals in mind:

* make the tool available on the web via a user friendly GUI
* make it less brittle, less buggy, and more consistent in its operation
* apply the analysis to a wider range of places (the original tool was confined to MA, CT, RI)
* enhance and enrich the data used in the analysis
* integrate the results with the larger CLF process


> The current, deployed tool can be found at:
>
> https://healthscore.pythonanywhere.com

***
How It Works
------------

You must have login credentials to use this site.

>Users and roles are managed here:
>
>https://healthscore.pythonanywhere.com/admin

Logged in users are presented with a text box where they can enter an address, anywhere in the U.S.
When they press "Next", the tool will geocode the address and return with a screen that displays
a variety of information about that location, including the state, county, census tract, and school
district (if data exists to do so.) There will also be a map, which shows the address marked at the
center of a circle, defined by a radius that can be changed. The map is interactive, and will respond
to mouseover actions by highlighting census tracts and displaying tooltips for census blocks.

All of this information, from the details of the location itself to the various parameters that
can be set (search radius, population threshold, housing data, etc.) from what is called a
**scorecard**. Scorecards can be titled, saved, and downloaded as an Excel spreadsheet. The spreadsheet
will contain data analysis for the primary census tract (that the address is located in) as
well as any others that meet the criteria specified in the search parameters. By default, this will
include any tracts that have at least 50% of their population (i.e. "population threshold") located
within the search radius visually indicated by the circle on the map. If a user belongs to the "Admin"
group, the downloaded spreadsheet will additionally contain a "master" tab that has the scoring
pre-filled from the raw data.

Users have the option to add or remove census tracts from the analysis, as well as change the default
search criteria to explore how the population is situated in that area. Saved scorecards will appear
under the "My Scorecards" tab and can be loaded with the previously used
parameters, edited, and re-saved.

***
Architecture and Implementation
-------------------------------

This tool uses a PostgreSQL database to store datasets that are used in the analysis, and is
implemented on the server-side with Python and Django. The front-end is implemented with HTML5, SASS,
and jQuery and/or plain old JavaScript. The tool relies on the Google geocoding service, as well as
a variety of Python-based libraries that retrieve and map census data. All other data is either
fetched on the fly from REST APIs or preloaded into the database using an import script.

***
Data Sources, Data Sets, and Vintages
-------------------------------

Healthscore uses a variety of data from external sources to support the analysis. Some of those data
only get used in the map view - some appear in the scorecard spreadsheet. Every category of data is
modeled in the application as a "data source". Most of these sources are periodically
updated and released to the public. That release day/month/year is modeled in the
application as a "vintage". A "data set" is the combination of a data source and a vintage, which
collectively refer to a particular release of that data. The metrics that are used from
data sets are usually a subset of what's available (i.e. those most relevant to this tool.)

Most of the datasets in the DB were imported from files that were downloaded from a webpage. However,
some sources are exposed through REST APIs and are used to dynamically retrieve data as needed
for a given location. Currently, those data sources are ACS, CDC, and EJ Screen.

***
Deployment and Production Environment
-------------------------------

The source control for this web application is a beanstalk repository owned by Tamarack Media.


>The source control url is:
>
>https://tamarack.git.beanstalkapp.com/clf-healthscore.git

This web application is meant to be developed locally (with a local instance of Postgres, but
it can be remote as well...) It is currently deployed on PythonAnywhere, using a Postgres instance
allocated and managed by PythonAnywhere. Deploying the app involves a
manual process that involves the following steps:

* Login to PythonAnywhere and open a bash console
* Change directory to "clf-healthscore" and perform a "git pull"
* <b>[Optional]</b> Change to directory "web" and perform "python manage.py migrate" or
"python import.py" if there have been DB schema changes or new data that needs to be added
* <b>[Optional]</b> Run "python manage.py collectstatic" to round up any new or updated images
* From the web console, reload the application

If styles or JS have been updated, you may need to clear the browser cache before reloading the
application to see the changes.


