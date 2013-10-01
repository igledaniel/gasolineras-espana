#!/usr/bin/env python

from shutil import copy
from urllib2 import urlopen, URLError, HTTPError
from datetime import date, timedelta
import os
import zipfile
import glob
import csv
import json
import re

def downloadFile(url):
    # Open the url
    try:
        _f = './zip/' + os.path.basename(url)
        if not os.path.exists(_f):
            f = urlopen(url)
            print 'downloading', url

            # Open our local file for writing
            with open(_f, 'wb') as local_file:
                local_file.write(f.read())

    # handle errors
    except HTTPError, e:
        print 'HTTP Error:', e.code, url
    except URLError, e:
        print 'URL Error:', e.reason, url

def extract():
    for _f in glob.glob('./zip/*.zip'):
        print _f
        zip_ref = zipfile.ZipFile(_f, 'r')
        zip_ref.extractall('./csv')
        zip_ref.close()
        # os.remove(_f)

def convertCsvToJson():
    for _f in glob.glob('./csv/*.csv'):
        filename = os.path.splitext(os.path.basename(_f))[0]
        print _f

        # export file to list
        lines = [line.strip() for line in open(_f)]
        i = 0
        jsonStack = []
        geoJsonStack = []

        # loop thrue lines
        for line in lines:
            i += 1
            # ignore 1st 2 lines
            if i < 3 or line == '':
                continue

            _line = line.split(',', 2)
            _json = {
                'lat': float(_line[0]),
                'lng': float(_line[1]),
                'name': '',
                'price': 0,
            }

            # TEXACO Horario Especial 1,009 e
            if _line[2].find('Horario Especial') != -1:
                matchObj = re.match(r'(.*) Horario Especial (\d,\d{3}) e', _line[2].strip()[1:])
                if matchObj:
                   _json['name'] = matchObj.group(1).strip()
                   price = matchObj.group(2).replace(',', '.')
                   _json['price'] = float(price)
                else:
                   print ' [ Not parsed] ', line
            # ESTACION DE SERVICIOS EL  L-D: 24H 0,997 e
            # THADER L-D: 24H 1,309 e
            # BTP L: 06:30-22:30 1,308 e
            else:
                matchObj = re.match(r'(.*) .*: .* (\d,\d{3}) e', _line[2].strip()[1:])
                if matchObj:
                   _json['name'] = matchObj.group(1).strip()
                   price = matchObj.group(2).replace(',', '.')
                   _json['price'] = float(price)
                else:
                   print ' [ Not parsed] ', line
            jsonStack.append(_json)
            geoJsonStack.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [_json['lat'], _json['lng']]
                },
                'properties': {
                    'name': _json['name'],
                    'price': _json['price']
                }
            })

        writeToJson(jsonStack, filename)
        writeToGeoJson({
            "type": "FeatureCollection",
            "features": geoJsonStack
        }, filename)

def writeToGeoJson(object, filename):
    _f = jsonFileName(filename, extraDir='geojson')
    print ' - writing to ' + _f
    with open(_f, 'w') as outfile:
        json.dump(object, outfile)
    copy(_f, './geojson/latest/')

def writeToJson(object, filename):
    _f = jsonFileName(filename)
    print ' - writing to ' + _f
    with open(_f, 'w') as outfile:
        json.dump(object, outfile)
    copy(_f, './json/latest/')

def jsonFileName(filename, extraDir='json'):
    matchObj = re.match(r'eess_(\S{3})_(\d{2})(\d{2})(\d{4})', filename)
    _dir = './'+extraDir+'/' + matchObj.group(4) + matchObj.group(3) + matchObj.group(2)
    if not os.path.exists(_dir):
        os.mkdir(_dir)
    return _dir + '/' + matchObj.group(1) + '.json'

def main():
    print '--- initialising'
    if not os.path.exists('./csv'):
        os.mkdir('./csv')
    if not os.path.exists('./json/latest'):
        os.makedirs('./json/latest')
    if not os.path.exists('./geojson/latest'):
        os.makedirs('./geojson/latest')
    if not os.path.exists('./zip'):
        os.mkdir('./zip')

    print '\n--- download zip files'
    yesterday = date.today() - timedelta(1)
    for petroltype in ['GPR', 'G98', 'GOA', 'NGO', 'BIO']:
        url = (
            'http://geoportal.mityc.es/'
            'hidrocarburos/files/'
            'eess_%s_%s.zip' % (
            petroltype,
            yesterday.strftime('%d%m%Y')
        ))
        downloadFile(url)

    print '\n--- extract'
    extract()

    print '\n--- convert csv to json'
    convertCsvToJson()

if __name__ == '__main__':
    main()