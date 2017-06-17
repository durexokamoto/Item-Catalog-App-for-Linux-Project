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
```.
12. Run 
```
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw limit 2200/tcp
sudo ufw allow 80/tcp
sudo ufw allow 123/udp
sudo ufw enable
```
to set firewall.
