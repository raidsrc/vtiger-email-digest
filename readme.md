# about

every time a vt project is created, the project data is sent to this server and stored in a db. the "queue."

also projects that are behind schedule get sent here all at once MWF morning around 5 AM PT. data on these projects is included in the project digest email.

every monday, wednesday, and friday morning at 7 AM PT, a cron job tells this server to send an email to our lab staff. the server fetches all the project data from the queue, formats it into a table, and sends an email to the lab staff summarizing the data. each project has a counter on it that is incremented by 1 each time the project is included in an email. it starts at 0 when a project is first added to the db.

another cron job comes immediately after, telling the server to trash all projects whose counter value is 2 or higher. this ensures that all projects that aren't behind schedule are included in 2 summary emails and no more.

yet another cron job comes after that telling the server to trash all projects where emailed_about=1&behind_schedule=true. this ensures all the behind schedule projects that have been emailed about once (in the email that was just sent) get trashed. 


# more about

get routes for viewing email settings and current queue
post routes for adding document to queue, triggering email
delete route for clearing queue

http basic auth secures the important endpoints. email, auth, and db are configured via .env

technology used: fastapi, mongodb atlas, postmark, vtiger workflows/webhooks, a bunch of other stuff

# automated testing

github actions for automated testing. starts a mongodb server in a docker container and runs tests using it.
pytest for testing.
you shouldn't need to run tests locally. aka please don't run tests locally. 