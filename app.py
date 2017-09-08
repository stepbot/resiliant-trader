from flask import Flask
from flask import jsonify
import pip

app = Flask(__name__)
@app.route('/')
def index():

	installed_packages = pip.get_installed_distributions()
	installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
	        for i in installed_packages])
	return jsonify(installed_packages_list)

if __name__ == "__main__":
	app.run()
