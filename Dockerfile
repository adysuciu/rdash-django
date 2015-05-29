####################################################
# Dockerfile to build Django-python container images
# Based on Ubuntu
####################################################    

# Set the base image to Ubuntu
FROM ubuntu

# File author
MAINTAINER Adrian Suciu

# Expose python port
EXPOSE 8080

USER root

# Update repository sources list
RUN apt-get update && apt-get install -y \
 gettext \
 git \
 libgettextpo-dev \ 
 libmysqlclient-dev \
 libsasl2-dev \
 libssl-dev \
 nodejs \
 node-less \
 npm \
 python-dev \
 python-setuptools

RUN easy_install pip
RUN pip install virtualenv
RUN pip install virtualenvwrapper

# Install bower
RUN npm config set registry http://registry.npmjs.org && npm install -g bower && ln -s /usr/bin/nodejs /usr/bin/node

# create application user
RUN useradd -g users -m -s /bin/bash rdash
RUN sudo su - rdash -c "mkdir ~/apps"
RUN sudo su - rdash -c "mkdir ~/apps/rdash"

# set env variables
ENV WORKON_HOME /home/rdash/envs
ENV PROJECT_HOME /home/rdash/apps/rdash

# virtualenv python runtime
RUN sudo su - rdash -c "echo 'export WORKON_HOME=${WORKON_HOME}' >> /home/rdash/.profile"
RUN sudo su - rdash -c "echo 'export PROJECT_HOME=${PROJECT_HOME}' >> /home/rdash/.profile"
RUN sudo su - rdash -c "echo 'source /usr/local/bin/virtualenvwrapper.sh' >> /home/rdash/.profile"
RUN sudo su - rdash -c "mkvirtualenv rdash"
# RUN sudo su - rdash -c "mkproject rdash"
RUN sudo su - rdash -c "echo 'workon rdash' >> /home/rdash/.profile"

# Add source code

#ADD . ${PROJECT_HOME}
RUN git clone https://github.com/adysuciu/rdash-django.git ${PROJECT_HOME}

# Environment info
ADD rdash/.env ${PROJECT_HOME}/rdash/.env

RUN chown -R rdash:users ${PROJECT_HOME}
RUN chmod 755 ${PROJECT_HOME}/manage.py

# Install django and dependencies
RUN sudo su - rdash -c "${WORKON_HOME}/rdash/bin/pip install -r ${PROJECT_HOME}/requirements.txt"
RUN sudo su - rdash -c 'echo {\"registry\":\"http://bower.herokuapp.com\"} > /home/rdash/.bowerrc'
RUN sudo su - rdash -c "python ${PROJECT_HOME}/manage.py bower_install"
RUN sudo su - rdash -c "python ${PROJECT_HOME}/manage.py collectstatic --noinput"
RUN sudo su - rdash -c "python ${PROJECT_HOME}/manage.py compilemessages"
RUN sudo su - rdash -c "python ${PROJECT_HOME}/manage.py makemigrations"
RUN sudo su - rdash -c "python ${PROJECT_HOME}/manage.py migrate"

ENTRYPOINT ["sudo","su","-","rdash"]
WORKDIR ${PROJECT_HOME}
# CMD ["sh","-c","python ${PROJECT_HOME}/manage.py runserver 0.0.0.0:8080"]