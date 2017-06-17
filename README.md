# Instrument Catalog App

I take a baseline installation of a Linux server, prepare it to host my web applications, secure my server from a number of attack vectors, install and configure a database server, and deploy one of my existing web applications onto it.

It is now can be access
<br>
http://34.210.70.238/
<br>
http://ec2-34-210-70-238.us-west-2.compute.amazonaws.com/



### How-to
1. Create the key pair locally using ```ssh-keygen```
2. Create an AWS lightsail instance with your existing public key.
3. run ```ssh -i ~/.ssh/privateKey ubuntu@34.210.70.238```You will be connected to the vm soon.
4. ```sudo su - root``` switch to the root user
5.
```
$useradd grader
$usermod -aG sudo grader
```
Create a user named grader and give him sudo access
<br>
6. 
```
mkdir /home/grader/.ssh
chown grader:grader /home/grader/.ssh
chmod 700 /home/grader/.ssh
cp /root/.ssh/authorized_keys /home/grader/.ssh/
chown grader:grader /home/grader/.ssh/authorized_keys
chmod 644 /home/grader/.ssh/authorized_keys
``` 
Copy ssh key for 'grader'
<br>
7. Logout and ```ssh -i ~/.ssh/privateKey grader@34.210.70.238```
Now you are connected via SSH as 'grader'.
<br>
8.
```
sudo nano /etc/ssh/sshd_config
```
Change default SSH port 22 to 2200 and change ```PermitRootLogin``` to ```PermitRootLogin no```.
<br>
9. Run ```service ssh restart``` to restart SSH and make it effective.<br>
10. Run ```sudo dpkg-reconfigure tzdata``` and set timezone to UTC.<br>
11. Update apps
```
sudo apt-get update
sudo apt-get upgrade
sudo reboot
```
12. Run
```
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw limit 2200/tcp
sudo ufw allow 80/tcp
sudo ufw allow 123/udp
sudo ufw enable
```
to set firewall.<br>
13. Logout and run ```ssh -i ~/.ssh/privateKey grader@34.210.70.238 -p 2200```You will be connected to the vm via 2200.<br>
14. Install required apps
```
sudo apt-get install apache2 libapache2-mod-wsgi postgresql
sudo apt-get install python-flask python-sqlalchemy python-pip
sudo apt-get install python-dev libpq-dev
sudo pip install psycopg2
sudo pip install oauth2client requests httplib2
sudo apt-get install git
```
15. Run
```
sudo git clone https://github.com/durexokamoto/Item-Catalog-App.git /var/www/app
```
Use git to clone your repository to the vm.<br>
16. Run
```
sudo -u postgres psql
create user catalog with password 'catalog';
create database catalog owner catalog;
revoke all on database catalog from public;
\q
```
Create database for the app.<br>
17. 
```
sudo nano /var/www/app/vagrant/seed.py
sudo nano /var/www/app/vagrant/application.py
```
Make sure the code is using PostgreSQL.<br>
18. enter /var/www/app/vagrant
```
sudo nano client_secrets.json
```
Make sure client_secrets.json has the correct config.<br>
19. Import the 'app' object as 'application'.
```
sudo nano application.wsgi
```
20. Allow www-data to write to /var/ww/app/vagrant/img directory.
```
sudo chown -R www-data:www-data img
```
21. Remove olf apache config
```
sudo rm /etc/apache2/sites-enabled/000-default.conf
sudo nano /etc/apache2/sites-available/catalog.conf
```
and create a new one as following
```
# Set server name.
ServerName ec2-x-x-x-x.us-west-2.compute.amazonaws.com

# Ensure the app has access to necessary modules.
WSGIPythonPath /var/www/app/vagrant

<VirtualHost *:80>
    # Point to the application's main Python script.
    WSGIScriptAlias / /var/www/app/vagrant/application.wsgi

    # Host the images.
    Alias /img/ /var/www/app/vagrant/img/

    # Host Flask's static directory.
    Alias /static/ /var/www/app/vagrant/static/
</VirtualHost>
```
22. Add the app to Apache2
```
sudo ln -s /etc/apache2/sites-available/catalog.conf /etc/apache2/sites-enabled
```
23. Restart Apache2 and then... enjoy
```
sudo apache2ctl restart
```
