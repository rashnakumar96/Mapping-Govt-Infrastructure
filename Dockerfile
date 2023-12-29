FROM python:3.9.14 

COPY scripts/ scripts/
COPY requirements.txt requirements.txt

# Build Chrome driver 
RUN apt-get update && \
    apt-get install -y gnupg wget curl unzip --no-install-recommends && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update -y && \
    wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_114.0.5735.90-1_amd64.deb && \
    CHROMEVER=$(google-chrome --product-version | grep -o "[^\.]*\.[^\.]*\.[^\.]*") && \
    echo $CHROMEVER && \
    DRIVERVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROMEVER") && \
    echo $DRIVERVER && \
    wget --continue -P /chromedriver "http://chromedriver.storage.googleapis.com/$DRIVERVER/chromedriver_linux64.zip"
RUN unzip /chromedriver/chromedriver* -d /chromedriver 

RUN cp chromedriver/chromedriver usr/bin/

# Install Java runtime 
RUN apt-get install -y default-jre

RUN pip3 install git+https://github.com/cisagov/findcdn.git
RUN pip install -r requirements.txt

ENTRYPOINT ["/bin/bash"]