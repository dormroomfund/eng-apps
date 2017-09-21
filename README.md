# Dorm Room Fund Engineering Applications

Thanks for your interest in applying to the DRF Engineering team! Our application is pretty simple.

Please submit a pull request to this repo with the following three things in a new directory `applications/$username`, where `$username` is your GitHub username.

You can see an example application [here](applications/yasyf).

### Basic Info

Please include the following information, in a valid JSON blob stored in `application.json`. Please use the keys in [the example](applications/yasyf/application.json).

  - First Name
  - Last Name
  - Email
  - University
  - Graduation Year
  - Resume (Link)
  - LinkedIn (Link)
  - Website (Link, Optional)
  - DRF Referral (Optional)

You can optionally encrypt this file using the instructions at the bottom of this document, in which case you would name the file `application.json.enc`.

### "Essay"

We want to get to know you a bit better! Include a paragraph or two in a file called `essay.md`, with the following information.

 - What do you like to hack on?
 - Which project are you most proud of?
 - What do you feel that you could get out of joining the DRF team?
 - Why are you uniquely capable of doing this job?
 - What's your most memorable characteristic?

You can optionally encrypt this file using the instructions at the bottom of this document, in which case you would name the file `essay.md.enc`.

### Challenge

We have the world's quickest coding challenge for you to do! In a subdirectory called `challenge`, please include your solution to the following.

> What is the most creative way you can get a circle to appear on the screen of a web browser?

Please include a run script (`run.sh`) which we can run to test your solution. This script should do any necessary building and compilation, and print either an address or a file we can open in a web browser running on the same machine. Make sure the script contains a valid shebang.

If you start a server, make sure you background it and have the script print out a URL to visit. If you start a server, please use the `$PORT` environment variable (which will be set for you) to determine which port to start the server on.

Please note, if you are calling `python` in your run script, you should be explicit about calling either `python2` or `python3`.

Alternatively, if your solution is a static site, you can simply include an `index.html` file and omit the run script.

## Encrypting Your Application

If you wish to conceal your personal information, you can encrypt individual files using the public key found in this repo ([`public.pem`](public.pem)). Please append the extension `.enc` to any file you encrypt. To encrypt a file, you can use the below command (make sure `openssl` is installed).

```bash
openssl smime -encrypt -aes256 -binary -in application.json -outform DEM -out application.json.enc public.pem
```

## Questions?

Shoot Yasyf an email (eng@drf.vc) if something looks wrong, broken, or confusing.
