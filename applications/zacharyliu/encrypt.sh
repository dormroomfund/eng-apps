#!/bin/bash
openssl smime -encrypt -aes256 -binary -in essay.md -outform DEM -out essay.md.enc ../../public.pem
