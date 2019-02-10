# mail
Minimal PyQt5 application to archive selected emails from an email application on a local drive.

Instructions:
1. Export the emails you want to archive from your mail app (e.g. in Mac OS X choose *File -> Save As* and then select 
   *Format: Plain text*).  This will create one large text file conatining the text from all the emails with each email 
   text separated by the `'\x0c'` character.
2. Run `python mailarchiver.py` on the command line.  This will open a PyQt dialog box that allows you to find and 
   select the text file from step 1.
3. Follow the prompts in the command line.  The content of each email is displayed in the PyQt window.
4. Every time it finds an email from an address that is not recognized you are prompted to choose a file location
   (folder) on your computer where you want to save emails from this person.  The convention used here is that the
   folder name should be the recognizable name of the sender (e.g. 'Jane Smith').  Folders are grouped into six sub-
   folder categories: 'Friends', 'Family', 'Acquaintances', 'Professional', 'Other', and 'To Delete'.
5. The folder name is then combined with the date of the email and the email is saved as a text file (e.g. 
   `'Jane Smith 2011 02 04 email.txt'`).

All subsequent emails from a known source will be saved in the same location automatically.

Note: This app does not deal with attachments.  You should manually remove attachments before or after archiving the
text using this app.
