from flask import Flask
from flask_restful import Api
from flask_cors import CORS, cross_origin

from poster import PosterMaker



def create_app():
    app = Flask(__name__)
    CORS(app)
    api = Api(app)

    # Endpoints
    api.add_resource(PosterMaker, '/poster')
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, passthrough_errors=False)