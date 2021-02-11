from flask import Flask, request, render_template
from flask_restful import Api, Resource, reqparse

from processor import convert_to_upper


app = Flask(__name__)
api = Api(app)

responder_put_args = reqparse.RequestParser()
responder_put_args.add_argument("comment", type=str, help="Please enter a comment.", required=True)


@app.route('/', methods=['GET','POST'])

def index():
    print(request.method)
    if request.method == 'POST':
        # For reference: get(<form name>) == <Form value>
        if request.form.get('submit_button') == 'Submit':
            # pass
            comment = request.form.get('comment')
            response = convert_to_upper(comment)
            print(response)
        else:
            # pass # unknown
            return render_template("index.html")
    elif request.method == 'GET':
        # return render_template("index.html")
        print("No Post Back Call")
    return render_template('index.html', response=response)


class Responder(Resource):
    def get(self,comment):
        return {"data": comment}



api.add_resource(Responder, "/comment/<string:comment>")

if __name__ == "__main__":
    app.run(debug=True)

