## Difficulty Logging In on Local Machine

### Issue
When attempting to authenticate using a Fedora login in a Flask application, an AttributeError is raised due to the usage of the deprecated `encodestring` attribute of the `base64` module. Additionally, after the app runs, the user faces server errors when logging in due to HTTPS configuration.

### Description
The AttributeError occurs because the `encodestring` attribute has been deprecated in Python 3 and replaced with `encodebytes`. Attempting to use `encodestring` results in an AttributeError. Furthermore, server errors occur when logging in due to the Flask application being configured to run over HTTPS.

### Cause
The root cause of the AttributeError is the usage of the deprecated `encodestring` attribute instead of `encodebytes` in the affected file. The server errors occur because the Flask application is configured to run over HTTPS by default.

### Solution
To resolve the AttributeError, replace `encodestring` with `encodebytes` in the affected file (`storage.py` within the `social_sqlalchemy` package). To resolve the server errors when logging in, change the Flask application configuration to run over HTTP instead of HTTPS.

### Steps to Resolve
1. Locate the file causing the AttributeError (`storage.py` within the `social_sqlalchemy` package).
2. Open the `storage.py` file in a text editor.
3. Search for the line causing the error: 
   ```
   assoc.secret = base64.encodestring(association.secret).decode()
   ```
4. Replace `encodestring` with `encodebytes`: 
   ```
   assoc.secret = base64.encodebytes(association.secret).decode()
   ```
5. Save the file.
6. Change the Flask application configuration to run over HTTP instead of HTTPS.



### Solution-2
To resolve the server errors when logging in, change the Flask application configuration to run over HTTP instead of HTTPS by modifying the `SERVER_NAME` configuration variable. Set the `SERVER_NAME` to use HTTP instead of HTTPS. Here's how you can do it:

Open the `wsgi.py` file in your Flask application directory.

Add the following line to set the `SERVER_NAME` configuration variable to use HTTP:
```
app.config['SERVER_NAME'] = 'http://localhost:5000'
```

Save the file.

After making this change, restart your Flask application, and it should now run over HTTP instead of HTTPS. This should resolve the server errors encountered when logging in.
If it persists, manually change the url from https to http

### References
- Python documentation: [base64.encodebytes](https://docs.python.org/3/library/base64.html#base64.encodebytes)