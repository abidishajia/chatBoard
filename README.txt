## Setup Project:
### Install Vagrant and VirtualBox
### Download or Clone this repository and cd into the folder

## Launch Project
### Launch the Vagrant VM using command:
  $ vagrant up
### Run your application within the VM
  $ python /vagrant/catalog/main.py
### Access and test your application by visiting http://localhost:5000.

# Log Analysis

### About

In this project, a large database with over a million rows is explored by building complex SQL queries to draw business conclusions for the data. 

### Setup
  Install Vagrant And VirtualBox
  Clone this repository

### To Run
  Launch Vagrant VM by running vagrant up, you can the log in with vagrant ssh
  To load the data, use the command psql -d news -f newsdata.sql to connect a database and run the necessary SQL statements.
  To execute the program, run python3 newsdata.py from the command line.
