# Item Catalog App

It's an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

### Prerequisites

  - VirtualBox
  - Vagrant
  - ubuntu-xenial
  - Python


### How-to
Make sure you cloned this repository under ```vagrant``` and load data ```newsdata.sql``` to ```news```.
Run your Terminal and ```cd ``` to where your ```vagrant``` files locates.

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
