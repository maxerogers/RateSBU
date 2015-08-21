#!flask/bin/python
from flask import Flask, jsonify, request, make_response, url_for
from flask.ext.restful import Api, Resource, reqparse
from lxml import html
from bs4 import BeautifulSoup
import urllib2, re, urlparse, json

app = Flask(__name__)
api = Api(app)

class RateMyProf(Resource):
    def get(self):
        return make_response(jsonify( { 'cat': 'no cute cat is implimented' } ), 200)
    def post(self):
        json_data = request.get_json(force=True)
        generated_response_in_json = generate_response(json_data)
        if generated_response_in_json:
            return ({'prof': generated_response_in_json})
        return ({'quality': 'no content'})
def generate_response(data):
    if data:
        AllProfQuality = []
        temp_cache = {}
        dup_name = [name.get('names')[0][0] for name in data['prof']]
        dup_name = list(set([name for name in dup_name if dup_name.count(name) > 1]))
        for name in dup_name:
            temp_cache[name.replace(' ', '')] = get_resources(str(name))
        for prof in data['prof']:
            _id = prof.get('id').replace('$', '\\$')
            for name in prof.get('names')[0]:
                if name in dup_name:
                    AllProfQuality.append({'id': _id, 'name': name , 'quality': temp_cache[name.replace(' ', '')]})
                else:
                    AllProfQuality.append({'id': _id, 'name': name , 'quality': get_resources(str(name))})
        return AllProfQuality
    return {'quality': 'error'}
      
def get_resources(name):
    base_url = "http://www.ratemyprofessors.com"
    url = (base_url + "/search.jsp?queryBy=teacherName&schoolName=stony+brook+university+suny&queryoption=HEADER&query="+str(name).replace(" ","%20"))
    try:
        req = urllib2.Request(url)
        get_html = urllib2.urlopen(req).read() 
        get_matched_link = re.search("(/ShowRatings.jsp\\?tid=\\d+)", get_html, re.IGNORECASE | re.MULTILINE)
        if get_matched_link:
            soup = BeautifulSoup(urllib2.urlopen(base_url + get_matched_link.group(1)).read(), 'lxml')
            tid = get_matched_link.group(1).split("=")[-1]
            return get_prof_quality(soup, tid)
        else:
            return {"quality": 'link not found'}
    except Exception, detail: 
        print "Error", detail 

def get_prof_quality(soup, tid):
    if soup: 
        overallQuality = []
        quality = {}
        for div in soup.select('div.breakdown-header'):
            quality_title = ''.join(div.contents[0].split())
            for quality_points in div.select('div.grade'):
                quality_points = quality_points.string
                if(quality_points == None):
                    quality_points = "http://www.ratemyprofessors.com" + div.findAll('img')[0]['src']
                quality[quality_title] = quality_points
        for div in soup.select('div.faux-slides div.rating-slider'):
            label = div.find('div', {'class': 'label'}).text
            rating = div.find('div', {'class': 'rating'}).text
            quality[label] = rating
        quality['tid'] = tid
        overallQuality.append(quality) 
        comments = get_student_comments(soup)
        if comments and overallQuality:
            overallQuality.append({'comments': comments})
            return overallQuality
        return {'quality': 'no quality'}
    return {'quality': 'invalid soup'}
    
def get_student_comments(soup):
    allComments = []
    comments_d = {}
    for tr in soup.select('tr[id]'):
        for date in tr.select('td.rating div.date'):
            comments_d["date"] = ''.join(date).strip()
        for at_class in tr.select('td.class span.name span.response'):
            comments_d["class"] = at_class.text
        for comments in tr.select('p.commentsParagraph'):
            comments = ''.join(comments).strip()
            comments_d["comment"] = comments
        if comments_d:
            allComments.append(comments_d)
    return allComments

@app.errorhandler(400)
def url_not_found(error):
    return make_response(jsonify( { 'cats': 'and dogs' } ), 400)

@app.errorhandler(404)
def url_not_found(error):
    return make_response(jsonify( { 'cat': 'meow' } ), 404)

api.add_resource(RateMyProf, '/', endpoint='/prof')
        
if __name__ == '__main__':
    app.run(debug = True)
