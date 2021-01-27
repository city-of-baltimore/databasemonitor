# databasemonitor
We have lots of databases that are periodically populated. This script notifies us if a database has not seen updates in an expected amount of time.

To run:
1. Setup a virtual environment:

       python -m venv .venv
   
2. Activate your virtual environment
   
    `.venv\Scripts\Activate` (Windows)
   
    `.venv/Scripts/activate.sh` (Linux)
   
3. Install all dependencies

       python -m pip install -r requirements.txt

   Also, install databasemonitor

       python setup.py install 

4. Adjust the main.py script to refer to the databases you want to monitor. The `config` variable is a list of dictionaries with the following values:

         table_name - name of the table to check
         date_col - datetime column to use as the critera
         email - email address to notify if it fails the check
         notification_secs - number of seconds of tolerance, outside of which will notify the email address
   
For example:

    [
        {
            'table_name': 'tabletomonitor', 
            'date_col': 'date_time',
            'email': 'brian.seel@baltimorecity.gov', 
            'notification_min': 60
        },
        ...  # repeat as necessary
    ]

4. Run the script

       python main.py --email_address <user> --email_password <pass> --smtp_server <server>

    Where `<user>` is the username to the email account to use to send notifications. `<pass>` should be the password to that account. `<server>` is the SMTP server address used to send notifications, which has the user/pass credentials. 
   
This is designed to work with a scheduled task or cron job to regularly check for database updates. 

## Testing
To run the test suite, run:

`python -m tox -e py39 -- --email_username bcdotnotifications@gmail.com --email_password eV^5d97%`

The same username/password is used for the SMTP server (to send email) and for the POP server (to check the email was received)
