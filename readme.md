# about

every time a vt project is created, the project data is sent to this server and stored in a db. the "queue."

every monday, wednesday, and friday morning, a cron job tells this server to send an email to our lab staff. the server fetches the all the project data for multiple projects from the queue, formats it into a table, and sends an email to the lab staff summarizing the data. each project has a counter on it that is incremented by 1 each time the project is included in an email. it starts at 0 when a project is first added to the db.

another cron job comes immediately after, telling the server to trash all projects whose counter value is 2 or higher. this ensures that all projects are included in 2 summary emails and no more.

# more about

get routes for viewing email settings and current queue
post routes for adding document to queue, triggering email
delete route for clearing queue

http basic auth secures the important endpoints. email, auth, and db are configured via .env

technology used: fastapi, mongodb atlas, postmark, vtiger workflows/webhooks, a bunch of other stuff