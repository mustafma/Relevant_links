from flask_bootstrap import Bootstrap
import json, sys
import requests
from time import sleep
from nbstreamreader import NonBlockingStreamReader as NBSR

from flask import Flask, render_template, request
import subprocess
import os
app = Flask(__name__)
bootstrap = Bootstrap(app)

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def StartEngine():
    proc = None
    with cd("relevant_page_finder/dist"):
        # we are in the jar library
        proc = subprocess.Popen(["java", "-jar","relevantpagefinder.jar" ], stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        print "Java engine is running"
    return proc

def is_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError, e:
    return False
  return True
proc = StartEngine()
# wrap p.stdout with a NonBlockingStreamReader object:
nbsr = NBSR(proc.stdout)
@app.route("/")
def main():
    return render_template('index.html', name='index')

@app.route('/query/',methods=['GET'])
def query():
    if request.method == 'GET':
        has_result = 0
        error = 0
        q = request.args.get('q')
        print "Query: " + q
        # 1. Send the search keyword to the java application
        # 2. Get the response as json:
        proc.stdin.write(q + "\r\n")
        proc.stdin.flush()
        # get the output
        output = nbsr.readline(900000)
        while (not is_json(output)):
            print output
            output = nbsr.readline(900000)
        # read the json
#        line = proc.stdout.readline()
#        print "python:" + line
#        while(line != "JSONRESULT\n"):
#            print "python: " + line
#            line = proc.stdout.readline()
#        # now read the json
#        line = proc.stdout.read()
#        print "python: " + line
        json_data = json.loads(output)

        if bool(json_data) :
            # print "results"
            print json.dumps(json_data, indent=4, sort_keys=True)
            result = []
            results = []
            # print(items)
            for item in json_data:
                result = {"title" : item['title'], "link" : item['url']}
                print "result " + result["title"]
                results.append(result)
                result = {}
            return render_template('index.html',q=q,results=results,error=error)
        else :
            return render_template('index.html',q=q,error=1)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run()
