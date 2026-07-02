# Games Meetup

A lightweight, mobile-first web app for arranging tabletop / board / card
game sessions with other players — online or at a local hobby shop.

Built with **Flask + SQLite** and designed to run at (close to) **zero
hosting cost**: no paid database, no paid cron service, no paid calendar
API.

## Features

- Register / log in / log out, with "forgot password" email recovery
- Create listings: game name, date & time, location (free-text **or**
  picked from an admin-managed Hobby Shop list), number of players needed
- Browse & filter open listings by game name / region
- Enroll in a listing with optional notes (faction, deck, etc.)
- Direct user-to-user messaging, optionally linked to a listing
- Close a listing once the game is arranged → emails everyone a
  confirmation with a `.ics` calendar attachment (works with Google
  Calendar, Outlook, Apple Calendar)
- Listings still open 3 days after their game date are **auto-closed**
  by an in-process background scheduler (no external cron needed)
- Admin-only page for basic DB maintenance: manage hobby shops, users,
  and listings
- Mobile-first responsive layout (bottom nav on phones, top nav on
  desktop)

## Project layout

```
games_meetup/
├── app.py                   # App factory + entry point
├── config.py                # Config from environment variables
├── extensions.py            # Shared Flask extension instances
├── models.py                # SQLAlchemy models (User, Listing, etc.)
├── forms.py                 # WTForms form classes
├── seed_shops.py            # Optional: pre-populate sample hobby shops
├── requirements.txt
├── .env.example              # Copy to .env and fill in real values
├── blueprints/
│   ├── auth.py               # register / login / password recovery
│   ├── listings.py           # create / browse / enroll / close
│   ├── messaging.py          # direct messages
│   └── admin.py               # admin-only maintenance routes
├── utils/
│   ├── email_utils.py         # Flask-Mail wrapper
│   ├── ics_utils.py            # .ics calendar file generation
│   └── scheduler.py             # APScheduler auto-close job
├── templates/                  # Jinja2 templates (mobile-first HTML)
├── translations/*              # Translation files
└── static/css/style.css         # Dependency-free, mobile-first CSS
```


## Become an admin ##
  The very first user who registers is
   automatically promoted to admin (or set `INITIAL_ADMIN_EMAIL` in
   `.env` to control exactly which email becomes admin). 

   Admin tools live at `/admin`.

## Sending real email (free options)

- **Gmail**: enable 2-Step Verification on a Gmail account, then
  create an "App Password" under Google Account → Security. Use that
  16-character password as `MAIL_PASSWORD`. Free, no cost.
- **Brevo (formerly Sendinblue)**: free tier includes 300 emails/day
  via SMTP, no credit card required for the free tier.

Either way, just fill in `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`,
`MAIL_PASSWORD` in `.env`.

## Deploying for free / near-free
Because everything (database + background scheduler) runs inside the
single Flask process, this app deploys cleanly to any small always-on
free/cheap tier, for example:

- **Render** (free web service tier, sleeps when idle) or a $7/mo
  starter instance if you want it always warm
- **PythonAnywhere** (free tier is fine for a small friend group)
- **Railway** / **Fly.io** (small free/hobby allowances)
- **Neon** / **Supabase** (for hosting a Postgres DB)

Notes for production:

- Set a real random `SECRET_KEY`.
- Run with a proper WSGI server instead of the Flask dev server, e.g.:

  ```bash
  pip install gunicorn
  gunicorn -w 1 -b 0.0.0.0:$PORT app:app
  ```

  (`-w 1` = 1 worker process. If you use more than 1 worker, be aware
  the in-process APScheduler job will run once per worker — for a
  small hobby app this is harmless, but if you want a single
  authoritative scheduler, run it as a separate `python -c "from
  app import create_app; ..."` worker, or just stick to 1 web worker
  since SQLite isn't built for heavy concurrency anyway.)

- SQLite is a single file — back it up periodically
  (`instance/games_meetup.db`) since most free hosts have ephemeral
  disks. If your host wipes the disk on redeploy, either use a host
  with a persistent volume (Render disks, Fly.io volumes) or point
  `DATABASE_URL` at a small free Postgres instance instead (the code
  already works unmodified with any SQLAlchemy-supported database URL).

## Notes on the code

- Every file is commented.
- CSRF protection (Flask-WTF) is enabled globally; every POST form
  includes a CSRF token, either via `form.hidden_tag()` for WTForms
  forms or a manual hidden `csrf_token` input for the small
  admin action forms (toggle/delete buttons).
- Passwords are hashed with Werkzeug's `generate_password_hash`
  (PBKDF2) — never stored in plain text.
- Password reset tokens are single-use and expire after 30 minutes.

## Translations
App is already translated to Portuguese, French and Spanish, if you
wish to translate to more languages:

-  Extract all marked strings into a template file
```
pybabel extract -F babel.cfg -k _ -k _l -o messages.pot .
```

- Initialize a new language (repeat per language)
```
pybabel init -i messages.pot -d translations -l de
pybabel init -i messages.pot -d translations -l it
```

- This creates translation files in:
```bash
/lang/LC_MESSAGES/messages.po   # This is the file that needs to be translated
```

- After translators fill in the .po files, compile them:
```
pybabel compile -d translations
```

- When you add/change strings later, re-extract and merge:
```
pybabel extract -F babel.cfg -k _ -k _l -o messages.pot .
pybabel update -i messages.pot -d translations
```
