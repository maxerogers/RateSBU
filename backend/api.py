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
        if json_data.get('prof'):
            if(isinstance(json_data['prof'][0].get('names'), list)):
                generated_response_in_json = generate_response(json_data)
                if generated_response_in_json:
                    return ({'prof': generated_response_in_json})
            else:
             return make_response(jsonify( { 'cats': 'bad cat' } ), 400)
        else:
             return make_response(jsonify( { 'cats': 'bad cat' } ), 400)

"""
- get prof link
- cache if name appear multiple times to avoid multiple requests
- return quality and comments
"""
def generate_response(data):
    comments_flag = False
    if data:
        AllProfQuality = []
        temp_cache = {}
        if data.get('comments'):
            comments_flag =data.get('comments')
        dup_name = [name.get('names') for name in data['prof']]
        dup_name = list(set([name for name in dup_name[0] if dup_name[0].count(name) > 1]))
        for name in dup_name:
            temp_cache[name.replace(' ', '')] = get_resources(str(name), comments_flag)

        for prof in data['prof']:
            _id = prof.get('id')
            if _id:
                _id = _id.replace('$', '\\$')
            for name in prof.get('names'):
                if name:
                    if name in dup_name:
                        get_from_cache = temp_cache[name.replace(' ', '')]
                        AllProfQuality.append({'id': _id, 'name': name ,'pid': get_from_cache[0] ,'quality': get_from_cache[1]})
                    else:
                        pid, quality = get_resources(str(name), comments_flag)
                        AllProfQuality.append({'id': _id, 'name': name , 'pid': pid, 'quality': quality})
        return AllProfQuality
    return make_response(jsonify( { 'quality': 'error' } ), 404)

"""
- check if professor exists in ratemp site and return quality/comments
"""
def get_resources(name, comments_flag):
    overallQuality = []
    base_url = "http://www.ratemyprofessors.com"
    url = (base_url + "/search.jsp?queryBy=teacherName&schoolName=stony+brook+university+suny&queryoption=HEADER&query="+str(name).replace(" ","%20"))
    try:
        req = urllib2.Request(url)
        get_html = urllib2.urlopen(req).read() 
        get_matched_link = re.search("(/ShowRatings.jsp\\?tid=\\d+)", get_html, re.IGNORECASE | re.MULTILINE)
        if get_matched_link:
            soup = BeautifulSoup(urllib2.urlopen(base_url + get_matched_link.group(1)).read(), 'lxml')
            tid = get_matched_link.group(1).split("=")[-1]
            quality_c = get_prof_quality(soup)
            if quality_c:
                overallQuality.append(quality_c)
            if comments_flag:
                overallQuality.append({'comments': get_student_comments(soup)})
            return (tid, overallQuality)
        else:
            return (404, {"quality": 'link not found'})
    except Exception, detail: 
        print "Error", detail 
        
"""
- get professor's quality i.e helpfulness / average grading
"""
def get_prof_quality(soup):
    if soup: 
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
        if quality:
            return quality
        return (404, {'quality': 'no quality'})
    return (404, {'quality': 'invalid soup'})

"""
- get student comments from professor profile
"""
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
    return make_response(jsonify( { 'cats': 'bad cat' } ), 400)

@app.errorhandler(404)
def url_not_found(error):
    return make_response(jsonify( { 'cat': 'meow' } ), 404)

api.add_resource(RateMyProf, '/')
        
if __name__ == '__main__':
    app.run(debug = True)
