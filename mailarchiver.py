"""Python script to archive emails from Mac Mail App
as text files on your local storage.

Instructions:
 - See README.md

"""

import os
import sys
import re
import yaml
from io import StringIO
import pandas as pd

import pyqt_files as pqt


def parse_emails_from_file(filename, path=None, divider_char="\x0c"):
    if path is not None:
        filename = os.path.join(path, filename)

    with open(filename) as f:
        file_contents = f.read()

    emails = file_contents.split(divider_char)

    print("File contains {:d} emails".format(len(emails)))

    return emails


def inspect_email_text(text):
    """Extracts key information from email header in text.

    Args:
        text: Raw email text including headers and body

    Returns:
        dict: Email data with fields From, Subject, Date, To, Body, etc.
              Returns None if required fields (From, Subject, Date) are missing.
    """
    sio = StringIO(text)
    required_fields = ["From", "Subject", "Date"]
    optional_fields = ["To", "Reply-To"]

    data = {"Subject": "", "To": ""}
    while True:
        line = sio.readline().rstrip()
        if line == "":
            break

        for field in required_fields + optional_fields:
            start_string = field + ": "
            if line.startswith(start_string):
                data[field] = line[len(start_string) :]

    missing_fields = [f for f in required_fields if f not in data]

    if missing_fields:
        print(f"Missing required fields: {missing_fields}")
        # Show preview of problematic email text
        preview = text[:200].replace("\n", "\\n")
        print(f"Email preview: {preview}...")
        return None

    if line == "":
        line = sio.readline().rstrip()

    data["Body"] = sio.readlines()

    return data


def find_email(line, lower=True):
    match = re.search(r"[\w\.-]+@[\w\.-]+", line)

    if match is not None:
        if lower is True:
            return match.group(0).lower()
        else:
            return match.group(0)
    else:
        return ""


def clean_text_for_display(text):
    """Clean up text for display by normalizing line endings and whitespace.

    Handles various line ending formats and problematic characters.
    """
    # Normalize line endings first
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Filter to printable characters, preserving newlines and tabs
    text = "".join(c if c.isprintable() or c in "\n\t" else " " for c in text)
    return text


def datetime_from_string(datestring, format=None):
    # Strip timezone abbreviations that pandas can't parse
    tz_abbrevs = [
        "PST",
        "PDT",
        "MST",
        "MDT",
        "CST",
        "CDT",
        "EST",
        "EDT",
        "GMT",
        "UTC",
    ]
    cleaned = datestring
    for tz in tz_abbrevs:
        cleaned = cleaned.replace(" " + tz, "").replace(tz, "")
    cleaned = cleaned.strip()

    try:
        dt = pd.to_datetime(cleaned, format=format)
    except ValueError:
        # This is needed to handle some dates which are
        # not valid. E.g.: July 18, 2008 at 24:48:37  PDT
        dt = pd.to_datetime(
            cleaned.replace("at 24:", "at 00:")
        ) + pd.Timedelta(1, unit="d")

    return dt


def get_email_datetime(email_text):
    """Extract datetime from raw email text for sorting.

    Args:
        email_text: Raw email text including headers

    Returns:
        tuple: (datetime or None, error_message or None)
    """
    # Quick parse to find Date field without full inspection
    for line in email_text.split("\n"):
        line = line.rstrip()
        if line == "":
            break
        if line.startswith("Date: "):
            date_str = line[6:]
            try:
                return datetime_from_string(date_str), None
            except (ValueError, TypeError) as e:
                return None, f"Could not parse date '{date_str}': {e}"
    return None, "No Date field found"


def sort_emails_by_date(emails):
    """Sort emails by datetime, with unparseable emails at the end.

    Args:
        emails: List of raw email texts

    Returns:
        list: Emails sorted by datetime (oldest first), with
              emails missing valid dates at the end
    """
    dated_emails = []
    undated_emails = []

    for email in emails:
        dt, error = get_email_datetime(email)
        if dt is not None:
            dated_emails.append((dt, email))
        else:
            print(f"Warning: {error}")
            undated_emails.append(email)

    # Sort by datetime (oldest first)
    dated_emails.sort(key=lambda x: x[0])

    # Return sorted emails, with undated ones at the end
    sorted_emails = [email for dt, email in dated_emails] + undated_emails

    if undated_emails:
        print(f"Note: {len(undated_emails)} email(s) without valid dates placed at end")

    return sorted_emails


def get_email_date_string(data, format="%Y %m %d"):
    """Extract and format the date from email data.

    Args:
        data: Dictionary containing email fields including 'Date'
        format: strftime format string for the output

    Returns:
        str: Formatted date string
    """
    try:
        dt = datetime_from_string(data["Date"])
    except ValueError:
        print("Date not recognized:", data["Date"])
        date_string = input("Enter date in '%s' format:" % format)
    else:
        date_string = dt.strftime(format=format)

    return date_string


def validate_email_db(email_db):
    """Validate and sort the email database.

    Performs the following checks:
    - Sorts entries alphabetically by email address
    - Verifies all entries have required keys: name, path, Last used
    - Validates paths are non-empty strings with valid path format

    Args:
        email_db: Dictionary mapping email addresses to contact info

    Returns:
        dict: Sorted and validated email database

    Raises:
        ValueError: If any entry is missing required keys or has invalid path
    """
    if not email_db:
        return email_db

    required_keys = {"name", "path", "Last used"}
    errors = []

    for email, entry in email_db.items():
        # Check for required keys
        if not isinstance(entry, dict):
            errors.append(f"'{email}': entry is not a dictionary")
            continue

        missing_keys = required_keys - set(entry.keys())
        if missing_keys:
            errors.append(f"'{email}': missing keys {missing_keys}")

        # Validate path is a non-empty string with valid format
        if "path" in entry:
            path = entry["path"]
            if not isinstance(path, str):
                errors.append(f"'{email}': path is not a string")
            elif path == "":
                errors.append(f"'{email}': path is empty")
            elif "\x00" in path:
                errors.append(f"'{email}': path contains null character")

    if errors:
        error_msg = "Email database validation errors:\n" + "\n".join(errors)
        raise ValueError(error_msg)

    # Sort entries alphabetically by email address
    sorted_email_db = dict(
        sorted(email_db.items(), key=lambda x: x[0].lower())
    )

    return sorted_email_db


def load_email_db(filename="email_db.yaml"):
    """Try to load address database if it exists.

    Note: YAML automatically handles duplicate keys by keeping the last
    occurrence, so duplicates are silently resolved during loading.
    """
    try:
        with open(filename, "r") as f:
            email_db = yaml.safe_load(f)
            if email_db is None:
                email_db = {}
    except FileNotFoundError:
        print("No address database found.")
        email_db = {}
    else:
        print("Address database loaded from file.")
        email_db = validate_email_db(email_db)
        print(f"Database validated: {len(email_db)} entries.")

    return email_db


def save_email_db(email_db, filename="email_db.yaml"):
    """Save address database."""

    with open(filename, "w") as f:
        yaml.dump(
            email_db,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    print("Address database saved to file '{}'.".format(filename))


def save_emails_to_file(emails, filename, path=None, divider_char="\x0c"):
    if path is not None:
        filename = os.path.join(path, filename)

    if len(emails) == 0:
        print("No emails to save")
        if os.path.isfile(filename):
            os.remove(filename)
        print("File deleted")
    else:
        file_contents = divider_char.join(emails)
        with open(filename, "w") as f:
            f.write(file_contents)

    print("{:d} emails saved back to file".format(len(emails)))


def save_email_to_text_file(filepath, name, date_string, email_content):
    """Save an email to a text file, handling filename conflicts.

    Naming strategy:
    - First email: 'Name YYYY MM DD email.txt' (no suffix)
    - Second email on same date: 'Name YYYY MM DDb email.txt'
    - Third email: 'Name YYYY MM DDc email.txt'
    - Through 'z', then continues with 'aa', 'ab', ..., 'az', 'ba', etc.
    - Supports up to 702 emails per day (1 + 25 + 676)

    If a file with the same name exists and contents are identical,
    no action is taken. If contents differ, the function finds the
    next available suffix starting from 'b'.

    Args:
        filepath: Directory to save the file in
        name: Name for the filename (e.g., person's name)
        date_string: Date string for the filename
        email_content: The email text to save

    Returns:
        str: Status message describing what happened
    """
    base_filename = "{:s} {:s} email.txt".format(name, date_string)
    full_path = os.path.join(filepath, base_filename)

    # Ensure the directory exists
    if not os.path.isdir(filepath):
        os.makedirs(filepath)

    # Helper to create suffixed filenames
    def make_suffixed_filename(suffix):
        return "{:s} {:s}{:s} email.txt".format(name, date_string, suffix)

    # Helper to get the next suffix in sequence
    def next_suffix(suffix):
        """Get next suffix: b, c, ..., z, aa, ab, ..., az, ba, ..., zz"""
        if len(suffix) == 1:
            if suffix == "z":
                return "aa"
            else:
                return chr(ord(suffix) + 1)
        else:
            # Two-letter suffix
            first, second = suffix[0], suffix[1]
            if second == "z":
                if first == "z":
                    return None  # Exhausted all suffixes
                return chr(ord(first) + 1) + "a"
            else:
                return first + chr(ord(second) + 1)

    # Helper to safely read file contents
    def safe_read_file(path):
        try:
            with open(path, "r", errors="ignore") as f:
                return f.read()
        except PermissionError:
            print(f"Warning: Cannot read '{path}' - permission denied")
            return None

    # Check if base file exists
    if not os.path.isfile(full_path):
        # No conflict, just save
        with open(full_path, "w") as f:
            f.write(email_content)
        return "Saved as '{}'".format(base_filename)

    # Base file exists - check if contents are identical
    existing_content = safe_read_file(full_path)

    if existing_content is not None and existing_content == email_content:
        return "Identical file already exists: '{}'".format(base_filename)

    # Contents differ - find next available suffix starting from 'b'
    suffix = "b"
    while suffix is not None:
        suffixed_filename = make_suffixed_filename(suffix)
        suffixed_path = os.path.join(filepath, suffixed_filename)

        if not os.path.isfile(suffixed_path):
            # Found an available filename
            with open(suffixed_path, "w") as f:
                f.write(email_content)
            return "Saved as '{}'".format(suffixed_filename)

        # File exists - check if contents are identical
        suffixed_content = safe_read_file(suffixed_path)
        if suffixed_content is not None and suffixed_content == email_content:
            return "Identical file already exists: '{}'".format(
                suffixed_filename
            )

        # Try next suffix
        suffix = next_suffix(suffix)

    # Exhausted all suffixes (more than 702 emails on one day)
    raise ValueError(
        "Exhausted all filename suffixes (more than 702 emails on one day)"
    )


# Default input and output file locations
DEFAULT_INPUT_PATH = os.path.join(
    os.path.expanduser("~"), "Desktop/Emails to file"
)
DEFAULT_SAVE_PATH = os.path.join(
    os.path.expanduser("~"), "Documents", "MyDocuments/People"
)

# Sub-folders for email storage
SUB_FOLDERS = {
    "Friend": "Friends",
    "Family": "Family",
    "Acquaintance": "Acquaintances",
    "Professional": "Professional",
    "Other": "Other",
    "Delete": "To delete",
    "Dating": "Dating",
}

# Email type options and folder names
KEY_CHOICES = {
    "f": "Friend",
    "m": "Family",
    "a": "Acquaintance",
    "p": "Professional",
    "o": "Other",
    "d": "Delete",
    "x": "Dating",
}


def main():
    """Main entry point for the email archiver application."""
    # Load email database if it exists
    email_db = load_email_db()

    app = pqt.QApplication(sys.argv)
    app.setStyle("macos")

    window = pqt.App("Email Archiver")

    # Select input text file
    input_file = window.openFileNameDialog(directory=DEFAULT_INPUT_PATH)

    if input_file == "":
        print("No file selected. Exiting.")
        sys.exit(0)

    emails = parse_emails_from_file(input_file)
    emails = sort_emails_by_date(emails)
    print(f"Emails sorted by date (oldest first)")
    emails_processed = []

    batch = 0
    for email in emails:
        if batch == 0:
            n = None
            print("Enter number of emails you want to process or 0 to quit.")
            while n is None:
                try:
                    n = int(input("> "))
                except ValueError:
                    n = None
            if n == 0:
                break
            batch = n

        data = inspect_email_text(email)
        if data is None:
            print("Skipping email with missing required fields")
            emails_processed.append(email)  # Mark as processed to remove it
            batch = batch - 1
            continue

        from_email = find_email(data["From"])
        print("\nProcessing email from", from_email)

        window.show_message("Email from: " + data["From"])
        window.show_text(clean_text_for_display(email))

        # Check if email address already known
        if from_email not in email_db:
            r = input("Email not known. Add to list (y/n)? ").lower()
            if r == "y":
                options = ["%s (%s)" % (v, k) for k, v in KEY_CHOICES.items()]
                option_text = ", ".join(options)
                while True:
                    r = input(option_text + " ? ")
                    if r in KEY_CHOICES or r == "q":
                        break
                    else:
                        print("Try again")
                if r == "q":
                    break

                group = KEY_CHOICES[r]

                path = os.path.join(DEFAULT_SAVE_PATH, SUB_FOLDERS[group])
                path = window.selectFolderNameDialog(directory=path)

                # Name is the name of the folder
                name = os.path.split(path)[-1]

                print("Saving path:", path)
                date_string = pd.Timestamp.now().strftime(format="%Y %m %d")
                email_db[from_email] = {
                    "name": name,
                    "path": path,
                    "Last used": date_string,
                }

            elif r == "q":
                break

        # Save email to file
        if from_email in email_db:
            name = email_db[from_email]["name"]
            filepath = email_db[from_email]["path"]
            date_string = get_email_date_string(data)
            result = save_email_to_text_file(
                filepath, name, date_string, email
            )
            print(result)

            emails_processed.append(email)
            batch = batch - 1

            if batch == 0:
                # Do a save of results
                save_email_db(email_db)
                emails = [
                    email for email in emails if email not in emails_processed
                ]
                save_emails_to_file(emails, input_file)

        else:
            print("Email was not added")

    save_email_db(email_db)

    emails = [email for email in emails if email not in emails_processed]
    save_emails_to_file(emails, input_file)

    window.show()
    print("Close window to exit.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
