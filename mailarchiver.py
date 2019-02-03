"""Python script to archive emails from Mac Mail App
as text files on your local storage.

Instructions:
 1. Before using this you need export the emails you want
    to archive as text files.  You can do this using the
    File -> Save As menu option and set the format to
    'Plain text'.  Select the emails you want to archive,
    and it will save them as one large text file.
"""

import os
import sys
import re
import json
from io import StringIO
import pandas as pd

import pyqt_files as pqt


def parse_emails_from_file(filename, path=None,
                           divider_char='\x0c'):

    if path is not None:
        filename = os.path.join(path, filename)

    with open(filename) as f:
        file_contents = f.read()

    emails = file_contents.split(divider_char)

    print("File contains {:d} emails".format(len(emails)))

    return emails

def inspect_email_text(text):
    """Extracts key information from email header in
    text.
    """

    sio = StringIO(text)
    required_fields = ["From", "Subject", "Date"]
    optional_fields = ["To", "Reply-To"]

    data = {'Subject': "", 'To': ""}
    while True:

        line = sio.readline().rstrip()
        if line == '':
            break

        for field in required_fields + optional_fields:
            start_string = field + ": "
            if line.startswith(start_string):
                data[field] = line[len(start_string):]

    tests = [field in data.keys() for field in required_fields]

    if not all(tests):
        print("Some required email fields were missing")
        import pdb; pdb.set_trace()

    if line == '':
        line = sio.readline().rstrip()
    else:
        import pdb; pdb.set_trace()
    data['Body'] = sio.readlines()

    return data

def find_email(line, lower=True):

    match = re.search(r'[\w\.-]+@[\w\.-]+', line)

    if match is not None:
        if lower is True:
            return match.group(0).lower()
        else:
            return match.group(0)
    else:
        return ""

def make_filename(name, email_address, data, email_db,
                  email, format="%Y %m %d"):

    try:
        date_string = pd.to_datetime(data["Date"]).strftime(format=format)
    except ValueError:
        # TODO: Some dates are not recognized
        # E.g.: July 18, 2008 at 24:48:37  PDT
        # should not be 24 hours!

        print("Date not recognized:", data["Date"])
        date_string = input("Enter date in 'Y m d' format: ")

    filename = "{:s} {:s} email.txt".format(name, date_string)

    # Check if file with same name already exists
    path = email_db[email_address]['path']

    try:
        existing_files = os.listdir(path)
    except FileNotFoundError as err:
        if not os.path.isdir(path):
            os.makedirs(path)
        else:
            # User may have pressed cancel
            raise err
    else:
        add_char = ''
        while filename in existing_files:

            # First see if file on disc is the same
            with open(os.path.join(path, filename), 'r') as f:
                other_file = f.read()

            if other_file == email:
                filename = None
                break
            else:
                # Modify the filename and try again until
                # it is unique
                filename = "{:s} {:s}{:s} email.txt".format(name,
                                                            date_string,
                                                            add_char)

                if add_char is '':
                    add_char = 'a'
                else:
                    add_char = chr(ord(add_char) + 1)
                    assert add_char != '{', "More than 26 emails on one day."

    return filename

def load_email_db(filename="email_db.json"):
    """Try to load address database if it exists.
    """

    try:
        with open("email_db.json", 'r') as f:
            email_db = json.load(f)
    except:
        print("No address database found.")
        email_db = {}
    else:
        print("Address database loaded from file.")

    return email_db

def save_email_db(email_db, filename="email_db.json"):
    """Save address database.
    """

    with open(filename, 'w') as f:
        json.dump(email_db, f)

    print("Address database saved to file '{}'.".format(filename))

def save_emails_to_file(emails, filename, path=None,
                        divider_char='\x0c'):

    if path is not None:
        filename = os.path.join(path, filename)

    if len(emails) == 0:
        print("No emails to save")
        if os.path.isfile(filename):
            os.remove(filename)
        print("File deleted")
    else:
        file_contents = divider_char.join(emails)
        with open(filename, 'w') as f:
            f.write(file_contents)

    print("{:d} emails saved back to file".format(len(emails)))


# Define default input and output file locations
user_path = os.path.expanduser("~")
input_path = os.path.join(user_path, "Desktop/Emails to file")
save_path = os.path.join(user_path, 'Documents', 'MyDocuments/People')

# Sub-folders for email storage
sub_folders = {
    'Friend': 'Friends',
    'Family': 'Family',
    'Acquaintance': 'Acquaintances',
    'Professional': 'Professional',
    'Other': 'Other',
    'Delete': 'To delete',
    'Dating': 'Dating'
}

# Email type options and folder names
key_choices = {
    'f': 'Friend',
    'm': 'Family',
    'a': 'Acquaintance',
    'p': 'Professional',
    'o': 'Other',
    'd': 'Delete',
    'x': 'Dating'
}

# Load email database if it exists
email_db = load_email_db()

app = pqt.QApplication(sys.argv)
app.setStyle('Macintosh')

window = pqt.App("Email Archiver")

# Select input text file
input_file = window.openFileNameDialog(directory=input_path)

emails = parse_emails_from_file(input_file)
emails_processed = []

batch = 0
for email in emails:

    if batch == 0:
        n = None
        print("Enter number of emails you want to process"
              " or 0 to quit.")
        while n is None:
            try:
                n = int(input("> "))
            except ValueError:
                n = None
        if n == 0:
            break
        batch = n

    data = inspect_email_text(email)
    from_email = find_email(data['From'])
    print("\nProcessing email from", from_email)

    window.show_message("Email from: " + data['From'])
    window.show_text(email[0:320])

    # Check if email address already known
    if from_email not in email_db:
        r = input("Email not known. Add to list (y/n)? ").lower()
        if r == 'y':
            options = ["%s (%s)" % (v, k) for k, v in key_choices.items()]
            option_text = ', '.join(options)
            while True:
                r = input(option_text + " ? ")
                if r in key_choices or r == 'q':
                    break
                else:
                    print("Try again")
            if r == 'q':
                break

            group = key_choices[r]

            path = os.path.join(save_path, sub_folders[group])
            path = window.selectFolderNameDialog(directory=path)

            # Name is the name of the folder
            name = os.path.split(path)[-1]

            print("Saving path:", path)
            date_string = pd.datetime.now().strftime(format="%Y %m %d")
            email_db[from_email] = {'name': name, 'path': path,
                                    'Last used': date_string}

        elif r == 'q':
            break

    # Save email to file
    if from_email in email_db:

        name = email_db[from_email]['name']
        filepath = email_db[from_email]['path']
        filename = make_filename(name, from_email, data,
                                 email_db, email)

        if filename is not None:
            with open(os.path.join(filepath, filename), 'w') as f:
                f.write(email)
        else:
            print("File already exists")

        emails_processed.append(email)
        batch = batch - 1

        if batch == 0:
            # Do a save of results
            save_email_db(email_db)
            emails = [email for email in emails if email not in
                      emails_processed]
            save_emails_to_file(emails, input_file)

    else:
        print("Email was not added")

save_email_db(email_db)

emails = [email for email in emails if email not in emails_processed]
save_emails_to_file(emails, input_file)

window.show()
print("Close window to exit.")

sys.exit(app.exec_())





