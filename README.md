# Dorm Room Fund Engineering Applications

Thanks for your interest in applying to the DRF Engineering team! Our application is pretty simple. Please submit a pull request to this repo with three things.

### Basic Info

Please include the following information, in a valid JSON blob stored in `application.json`. Please use the keys in [the example](example/application.json). You can optionally encrypt this file using the instructions at the bottom of this document, in which case you would name the file `application.json.enc`.

  - First Name
  - Last Name
  - Email
  - University Name

### "Essay"

We want to get to know you a bit better! Include a paragraph or two in a file called `essay.txt`, with the following information.

 - What do you like to hack on?
 - Which project are you most proud of?
 - What do you feel that you could get out of joining the DRF team?
 - Why are you uniquely capable of doing this job?
 - What's your most memorable characteristic?

### Challenge

We have the world's quickest coding challenge for you to do! In a directory called `challenge`, please include your solution to the following.

> What is the most creative way you can get a circle to appear on the screen of a web browser?

Please include a run script (`run.sh`) which we can run to test your solution. This script should do any necessary building and compilation, and print either an address or a file we can open in a web browser running on the same machine.

## Encrypting Your Application

If you wish to conceal your personal information, you can encrypt individual files using the public key found in this repo ([`public.pem`](public.pem)). Please append the extension `.enc` to any file you encrypt. To encrypt a file, you can use the below command (make sure `openssl` is installed).

```bash
openssl rsautl -encrypt -inkey public.pem -pubin -in application.json -out application.json.enc
```
