# Instrument Catalog App

I take a baseline installation of a Linux server, prepare it to host my web applications, secure my server from a number of attack vectors, install and configure a database server, and deploy one of my existing web applications onto it.

It is now can be access
<br>
http://34.210.70.238/
<br>
http://ec2-34-210-70-238.us-west-2.compute.amazonaws.com/



### How-to
1. Create the key pair locally using ```ssh-keygen```

```sh
$ vagrant ssh
$ cd /vagrant
$ cd Item-Catalog-App
$ python database_setup.py
$ python lotsofmenus.py
$ python project.py
```
Open your prefered browser and vist the site via
```
http://localhost:5000/
```
or
```
http://0.0.0.0:5000/
```
