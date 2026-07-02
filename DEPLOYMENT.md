# Games Meetup
To host the solution outside of your local Network/Dev environment at the lowest cost possible

## Web Hosting
https://render.com/

Create a project and link it to GitHub, this will ensure automated deploys take place

On render we need to add the contents of the .env file in:  \Environment\Secret Files

DATABASE_URL is the base minimum but the other setting should be present as well

On \Environment

Optionally set a variable called PYTHON_VERSION to 3.13 (it's already mentioned on .python-version file)

Set the Start Command to:
		gunicorn app:app --workers=1	(Only one worker to prevent issues with background scheduler)

## Database Hosting

https://neon.com/

Create a project/database (use Neon's Connection Pooling to avoid issues with the Scheduler)

Set the connection string in "DATABASE_URL=" on your .env