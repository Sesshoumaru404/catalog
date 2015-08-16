###Project 2: Swiss Tournament
The Item Catalog project consists of developing an application that provides a list of items within a variety of categories, as well as provide a user registration and authentication system with API endpoint JSON and ATOM. In this sample project, the homepage displays all current categories along with the latest added items. This project also had the add functionality of be able to store store images for an item. Post request are also protect against prevent cross-site request forgeries.

###Files
| File | Description |
|------|-------------|
| **catalog.py** | This files is uses SQLAlchemy to configure the database for this website. |
| **project.py** |  This files houses most of the configuration and also used to run application |
| **fakeitems.py** | Use this file to add test data to your database. |
| **helpers.py** | File contains helper functions for this python application. |
| **client_secrets.json** | Must update this file with your Google info and also '/static/login.html' line 14 'data-clientid'. |
| **Vagrantfile** | This is file is used to create virtual box to run project in. |
| **pg_config.sh** | This is file is used to configure your virtual box. |
| **/images/** | This folder holds all the item related images. |
| **/static/css/** | This folder holds all CSS style files for the website. |
| **/static/js/** | This folder holds all JavaScript files for the website. |
| **/templates/** | This folder holds all html files for the website |

###Requirements
* Virtual Box - [download](https://www.virtualbox.org/wiki/Downloads)
* Vagrant - [download](https://www.vagrantup.com/downloads)

####Installation Steps:
1. Download project:
  - Linux: Open terminal the type `git clone https://github.com/Sesshoumaru404/catalog.git`
2. Move to project folder:
  - Linux: Type `cd catalog`
3. Turn on the virtual machine:
  - Linux: Type `vagrant up`
  - Linux: Followed by `vagrant ssh`
  - You are now in your Virtual Machine.
4. Move to the *tournament* folder:
  - Vagrant terminal: Type `cd /vagrant`
5. To populate database:
  - Vagrant terminal: Type `python fakeitems.py`
  - When complete console will display `Added items!`
5. Start server:
  - Vagrant terminal: Type `python fakeitems.py`
  - When running console will display
  ```
  * Running on http://0.0.0.0:5000/
  * Restarting with reloader
  ```
6. Go to browser and enter `http://localhost:5000/`


###Tests
1. Sign in with Google - first user to sign-in gains Admin status
2. Create a item.
3. Delete a item.
4. Add a picture to existing item
5. Try to edit a post without being logged in.
6. Try a feed.
7. Sign as another user to view change in pages.
8. Try to break application, if does break please open an issue so I can fix it.

###Verisons

Python 2.7.6
Vagrant 1.7.2
Virtual Box 4.3.10

###License

MIT
