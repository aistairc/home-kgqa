#!/usr/bin/env python
# coding: utf-8

import sys
import json
from rdflib import *
import glob
import os
import re
from SPARQLWrapper import SPARQLWrapper, JSON, BASIC


def getSPARQLResults(queryString, scene):
    result = None
    sparql = SPARQLWrapper("http://localhost:7200/repositories/vhakg-episode-" + scene)
    sparql.setQuery(queryString)
    sparql.setReturnFormat(JSON)
    try :
        json = sparql.query().convert()
        bindings = json['results']['bindings']
        result = bindings
    except  Exception as e:
        print(e)
    return result


scene = "scene1"
prefix = """
PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
"""
query_different_locations = """
        {}
        select distinct ?s ?roomBefore ?roomAfter where {{ 
            ?s	:action ?action ;
                :mainObject ?object ;
                :agent ?agent ;
                :situationBeforeEvent ?before ;
                :situationAfterEvent ?after .
            ?agentBeforeState :isStateOf ?agent ;
                              :partOf ?before ;
                              :bbox ?agentBeforeBbox .
            ?agentAfterState :isStateOf ?agent ;
                             :partOf ?after ;
                             :bbox ?agentAfterBbox .
            ?agentBeforeBbox :inside ?roomBeforeBbox .
            ?agentAfterBbox :inside ?roomAfterBbox .
            ?roomBeforeState :bbox ?roomBeforeBbox ;
                       :isStateOf ?roomBefore ;
                       :partOf ?before .
            ?roomAfterState :bbox ?roomAfterBbox ;
                            :isStateOf ?roomAfter ;
                            :partOf ?after .
            ?roomBefore a [rdfs:subClassOf :Room ] .
            ?roomAfter a [rdfs:subClassOf :Room ] .
            filter (?roomBefore != ?roomAfter)
        }}
    """.format(prefix)

query_events_and_places = """
        {}
        select distinct ?s ?room where {{ 
            {{
                ?s :mainObject ?object ;
                    :situationBeforeEvent ?before .
                ?state :isStateOf ?object ;
                       :partOf ?before ;
                       :bbox ?shape .
                ?shape :inside ?roomShape .
                ?roomState :bbox ?roomShape ;
                           :isStateOf ?room .
                ?room a [rdfs:subClassOf :Room] .
            }} UNION {{
                ?s :mainObject ?room .
                ?room a [rdfs:subClassOf :Room] .
            }}
        }}
    """.format(prefix)
json_events_from_to = getSPARQLResults(query_different_locations, scene)
json_events_and_places = getSPARQLResults(query_events_and_places, scene)



base = Namespace("http://kgrc4si.home.kg/virtualhome2kg/instance/")
onto = Namespace("http://kgrc4si.home.kg/virtualhome2kg/ontology/")
events_different_locatins = {}
for result in json_events_from_to:
    event = result["s"]["value"]
    from_location = result["roomBefore"]["value"]
    to_location = result["roomAfter"]["value"]
    events_different_locatins[event] = {"from": from_location, "to": to_location}

g = Graph()
for result in json_events_and_places:
    event_uri = result["s"]["value"]
    place_uri = result["room"]["value"]
    event_r = URIRef(event_uri)
    place_r = URIRef(place_uri)
    if event_uri in events_different_locatins:
        from_location_r = URIRef(events_different_locatins[event_uri]["from"])
        to_location_r = URIRef(events_different_locatins[event_uri]["to"])
        g.add((event_r, onto["from"], from_location_r))
        g.add((event_r, onto["to"], to_location_r))
    else:
        g.add((event_r, onto.place, place_r))

g.bind("ex", base)
g.bind("vh2kg", onto)
output_path = "./dataset/kg/add_places.ttl"
g.serialize(destination=output_path, format="turtle")