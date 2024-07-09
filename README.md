# Test It
#### Video Demo:  <https://youtu.be/AfnrL-dQPKg>
#### Description: web application. creating bussines model and profit and loss forecast

Application will help to create a business model without a deep understanding of finance.
Key issue to provide for users friendly and simple interface. For example, a person without a finance background can answer questions in forms and complete business models and profit and loss forecasts in less than 30 minutes.

From the user's point of view I picked card format as questions form.
application consists of 5 steps, each step represented in a own page and has cards with blocks of questions. each block grouped logically. The main page represents consolidated brief information from each step.

Before the application starts, users have to register. Registration necessary to store user data in the database. Database stored seven tables for different tasks.

after registration and login which code described in @app.route("/register")
 and @app.route("/login"), index page redirect users to the first step. Redirecting necessary to avoid displaying empty cards on the index page. If the user already fills the forms index will display dashboard style information.

The first step is called “our client”. server code @app.route("/client") and front side rendered via client.html.  This step has 4 cards. our client, our product, our check and client avatar.
The first three cards used bootstrap input forms to get values from the user. in the third and fourth card java script calculates data. i choose java script for this purpose to avoid connection to serve for simple calculations. This script allows fast and often changing the input data to observe potential results. If the user is satisfied with inserted data, the “save” button passes data to the server via post method. on server side data inserted via sql insert command to “client” table. After that the user is redirected to the second step.

In case the user previously inserted data about the client, server side code passed value to html side and javascript change button name for “delete data and add new”. this script allow user to delete stored data and start new project.

The second step is called the revenues model.  server code @app.route("/rev"), rendered in rev.html. As a previous step it used the post method to get values from the user, and get method to use previously inserted data in our client page. In the first step we collect data about potential customers and calculate average check and frequency of deals. Using this data we forecast our revenue from this product multiplying by the number of potential customers. This part is realized in javascript and online displayed in the third card “total revenues”. In the second card we insert other revenues and java script choose type of calculation dependly of users choice of type of other revenues. In this card I also realized button  which called the post method, but it linked to @app.route("/other_rev"). In real life there could be several different types of other revenues, and this code calculates and stores in table each and allows to add new. The final button “save” runs the post method on @app.route("/rev") which stores main revenue in table revenues.

“Expenses model” step is similar to the “revenues model”, but inside of server side calculations and java script use more complex formulas, because expenses depend on revenues. For this reason this step gets data from previous steps and calculates new values, which are displayed and stored with the same logic as in the previous step.

The fourth step is the biggest in terms of code and more complex than others. Code @app.route("/plforecast") and rendered in plforecast.html. Main function of this step is to create a profit and loss forecast for 12 months.  At this moment I realized one scenario of forecasting which supposed constant monthly growth till model values. For this purpose an application designed to collect and update previously inserted data. Users insert only one variable - growth rate. Variable used for calculations of new values which stored in table “plforecast”.  via jinja dataset passed to loop in plforecast.html and render table for values in 12 month period. Financial result for 12 months stored in pl table.In the future, it's possible to add new different scenarios for forecasting.


The fifth step @app.route("/canvas") rendered in canvas.html.  9 cards describe key parts of any business model. They will help to structure business models. To store data in the “canvas” table use the post method.

Saving the last step redirects to the index page. Where in dashboard style rendered all previous steps. all data grouped logically in cards.  Chart.js visualizes monthly results in PL chart. Via java script, the clear button calls @app.route("/index_clr") to clear all data connected with the current user. This function allows to clear all data and start new modeling.

