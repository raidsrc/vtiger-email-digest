# about

For a long time, the laboratory teams in charge of cloning, viral vector manufacturing, and other stuff at Virovek would get inundated with emails from our CRM/project management software (Vtiger) about new projects being created. We had it set up to send emails whenever a new project was created. Sometimes they'd receive 50 emails in their inbox, triggered by the creation of 50 new projects. This wasn't working for them. So I built this.

## summary

* every time a vt project is created, the project data is sent to this server and stored in a db. the "queue."
* also projects that are behind schedule get sent here all at once MWF morning around 5 AM PT. data on these projects is included in the project digest email.
* every monday, wednesday, and friday morning at 7 AM PT, a cron job tells this server to send an email to our lab staff. the server fetches all the project data from the queue, formats it into a table, and sends an email to the lab staff summarizing the data. each project has a counter on it that is incremented by 1 each time the project is included in an email. it starts at 0 when a project is first added to the db.
* another cron job comes immediately after, telling the server to trash all projects whose counter value is 2 or higher. this ensures that all projects that aren't behind schedule are included in 2 summary emails and no more.
* yet another cron job comes after that telling the server to trash all projects where emailed_about=1&behind_schedule=true. this ensures all the behind schedule projects that have been emailed about once (in the email that was just sent) get trashed. 

And just like that, instead of 50 emails for 50 projects, the laboratory teams receive a single email 3 times a week summarizing all of the projects they need to keep tabs on.

And yes, the laboratory teams have let me know that they love it. 😁

## slightly technical details

* get routes for viewing email settings and current queue
* post routes for adding document to queue, triggering email
* delete route for clearing queue
* http basic auth secures the important endpoints
* email, auth, and db are configured via .env
* pretty much everything important configured via .env 

### technologies used
* fastapi
* mongodb atlas
* postmark
* vtiger workflows/webhooks
* a bunch of other stuff

FastAPI is amazing, dude. Coming from someone who's done a lot of full stack in Node, I have to say... FastAPI just works, and it's so great. Node/Express is great too, but I got up and running in the blink of an eye with FastAPI. I think it would've taken me a little bit longer with Node, despite having worked with it for longer.

### oh yeah, github actions for automated testing too
* github actions for automated testing. starts a mongodb server in a docker container and runs tests using it.
* pytest for testing.
* you shouldn't need to run tests locally. aka please don't run tests locally. 