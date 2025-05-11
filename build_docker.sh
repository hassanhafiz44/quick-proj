# in case it's currently app
docker stop flask-app
docker remove flask-app

docker build . -t flaskr
docker run -d -p 5000:5000 --name flask-app flaskr