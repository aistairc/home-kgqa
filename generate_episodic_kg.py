#!/usr/bin/env python
# coding: utf-8

import os
import csv
import random
import re
import glob
import datetime
import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON, BASIC

# Constants and Configuration
ACTIVITY_CLASS_MAP = {
    "就寝・起床": "BedTimeSleep",
    "飲食": "EatingDrinking",
    "飲食準備": "FoodPreparation",
    "整理・整頓": "HouseArrangement",
    "清掃・洗浄": "HouseCleaning",
    "衛生": "HygieneStyling",
    "娯楽": "Leisure",
    "仕事・学業": "Work",
    "身体活動": "PhysicalActivity",
    "その他": "Other"
}

EPISODE_NUM = 5
SCENE = "scene1"
INIT_TIME = datetime.datetime(2024, 4, 1, 5, 00, 00)

# Data loading
cs_results = []
with open("data/lancers_task.csv", encoding="utf-8", newline="") as f:
    for cols in csv.reader(f, delimiter=","):
        cs_results.append(cols)
#delete header
cs_results.pop(0)


# Data Processing Functions
def convert_name(table):
    result = []
    for line in table:
        new_line = []
        for x in line:
            new_line.append(ACTIVITY_CLASS_MAP[x])
        result.append(new_line)
    return result


def add_start_end(sequence):
    tmp = ['start']
    tmp.extend(sequence)
    tmp.extend(['end'])
    return tmp




# Markov Chain Functions
def create_ngram(sequence_list):    
    ngram = {}
    for seq in sequence_list:
        for i in range(19):
            if seq[i] in ngram:
                values = ngram[seq[i]]
                if seq[i+1] in values.keys():
                    values[seq[i+1]] += 1
                else:
                    values[seq[i+1]] = 1
                ngram[seq[i]] = values
            else:
                tmp = {}
                tmp[seq[i+1]] = 1
                ngram[seq[i]] = tmp
    return ngram


def create_transition_probability(ngram):    
    transition_probability = {}
    for current_activity in ngram:
        next_activities = ngram[current_activity]
        num = 0
        for na_key in next_activities:
            num += next_activities[na_key]
        probability = {}
        for na_key in next_activities:
            probability[na_key] = next_activities[na_key] / num
        transition_probability[current_activity] =probability
    return transition_probability


def markov_chain(transition_probability):    
    current_activity = "start"
    activity_list = []
    for i in range(18):
        next_candidates = {}
        next_candidates = transition_probability[current_activity]

        keys = []
        values = []
        for x in next_candidates:
            keys.append(x)
            values.append(next_candidates[x])
        next_activity = random.choices(
            population=keys,
            weights=values
        )
        current_activity = next_activity[0]
        if current_activity == "end":
            break
        activity_list.append(current_activity)
    return activity_list




# Ontology Functions
def get_activity_from_ontology(activity_type, scene):
    print(activity_type)
    result = None
    queryString = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
        PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
        select distinct ?activity where {{ 
            ?activity a ?activityClass ;
                vh2kg:virtualHome ex:{} .
            ?activityClass rdfs:subClassOf ho:{} . 
         }} ORDER BY RAND() limit 1 
    """.format(scene, activity_type)
    sparql = SPARQLWrapper("http://localhost:7200/repositories/vhakg")
    # sparql.setHTTPAuth(BASIC)
    # sparql.setCredentials('admin', '')
    sparql.addParameter('infer', 'true')
    

    sparql.setQuery(queryString)
    sparql.setReturnFormat(JSON)

    try :
        json = sparql.query().convert()
        bindings = json['results']['bindings']
        if len(bindings) > 0:
            result = bindings[0]
    except  Exception as e:
        print(e.args)
    return result


def export(routine_list, scene):
     with open(f"episode_list_{scene}_{str(EPISODE_NUM)}.txt", 'w') as f:
            for routine in routine_list:
                f.write("%s\n" % ','.join(routine))


# RDF Processing Functions
def get_events_with_duration_from_activity(g, activity):
    queryString = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
PREFIX time: <http://www.w3.org/2006/time#>
select distinct ?event ?event_num ?duration where {{ 
    <{}> :hasEvent ?event .
    ?event :eventNumber ?event_num ;
           :time/time:numericDuration ?duration .
}} order by asc(?event_num)
""".format(activity)
    results = g.query(queryString)
    return results


def updateEKGURI(text, activity, id):
    ex = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
    new_activity = activity.replace(ex, "ex:") + "-" + str(id)
    text = text.replace(activity.replace(ex, "ex:"), new_activity)
    text = re.sub(r"ex:event([\w\-]+)", "ex:event\\1-" + str(id), text)
    text = re.sub(r"ex:state([\w\-]+)", "ex:state\\1-" + str(id), text)
    text = re.sub(r"ex:shape([\w\-]+)", "ex:shape\\1-" + str(id), text)
    text = re.sub(r"ex:home_situation([\w\-]+)", "ex:home_situation\\1-" + str(id), text)
    text = re.sub(r"ex:time([\w\-]+)", "ex:time\\1-" + str(id), text)
    return text


def updateMMKGURI(text, activity, id):
    ex = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
    # activity_name = activity.replace(ex, "")
    new_activity = activity.replace(ex, "ex:") + "-" + str(id)
    text = text.replace(activity.replace(ex, "ex:") + " ", new_activity + " ")
    text = re.sub(r"ex:([\w\-]+)_scene(\d)_camera(\d)([\s,])", "ex:\\1_scene\\2_camera\\3-" + str(id) + "\\4", text)
    text = re.sub(r"ex:([\w\-]+)_(\d)_scene(\d)_video_segment([\d]+)([\s,])", "ex:\\1_\\2_scene\\3_video_segment\\4-" + str(id) + "\\5", text)
    text = re.sub(r"ex:([\w\-]+)_(\d)_scene(\d)_frame([\d]+)([\s,])", "ex:\\1_\\2_scene\\3_frame\\4-" + str(id) + "\\5", text)
    text = re.sub(r"ex:([\w\-]+)_(\d)_scene(\d)_frame([\d]+)_([\w]+)([\s,])", "ex:\\1_\\2_scene\\3_frame\\4_\\5-" + str(id) + "\\6", text)
    text = re.sub(r"ex:([\w\-]+)_(\d)_scene(\d)_video_segment([\d]+)_start_time([\s,])", "ex:\\1_\\2_scene\\3_video_segment\\4_start_time-" + str(id) + "\\5", text)
    text = re.sub(r"ex:([\w\-]+)_(\d)_scene(\d)_video_segment([\d]+)_end_time([\s,])", "ex:\\1_\\2_scene\\3_video_segment\\4_end_time-" + str(id) + "\\5", text)
    text = re.sub(r"ex:event([\w\-]+)", "ex:event\\1-" + str(id), text)
    return text


def exportEpisodeRDF(g, scene, episode_num):
    ex = rdflib.Namespace("http://kgrc4si.home.kg/virtualhome2kg/instance/")
    g.bind("ex", ex)
    print("export episode: ", episode_num)
    g.serialize(destination=f"kg/{scene}/episode{str(episode_num)}_{scene}_v2.ttl", format='turtle')


def fixFileName(file_path):
    if "Drink_wine_while_watching_television" in file_path:
        file_path = file_path.replace("Drink_wine_while_watching_television", "Drink_wine_while watching_television")
        return file_path
    if "Eat_bread_while_watching_television" in file_path:
        file_path = file_path.replace("Eat_bread_while_watching_television", "Eat_bread_while watching_television")
        return file_path
    if "Drink_milk_while_watching_television" in file_path:
        file_path = file_path.replace("Drink_milk_while_watching_television", "Drink_milk_while watching_television")
        return file_path

    return file_path


# Main Execution Functions
def create_episode_rdf(routine_list, init_time):
    
    init = True
    id = 0
    current_time = init_time
    for episode_num in range(len(routine_list)):
        g = rdflib.Graph()
        vh2kg = rdflib.Namespace("http://kgrc4si.home.kg/virtualhome2kg/ontology/")
        time = rdflib.Namespace("http://www.w3.org/2006/time#")
        ho = rdflib.Namespace("http://www.owl-ontologies.com/VirtualHome.owl#")
        ex = rdflib.Namespace("http://kgrc4si.home.kg/virtualhome2kg/instance/")
        mssn = rdflib.Namespace("http://mssn.sigappfr.org/mssn/")
        schema = rdflib.Namespace("http://schema.org/")
        sosa = rdflib.Namespace("http://www.w3.org/ns/sosa/")
        routine = routine_list[episode_num]
        episode_r = ex["episode" + str(episode_num)]
        g.add((episode_r, rdflib.RDF.type, vh2kg.Episode))
        for activity_num in range(len(routine)):
            activity = routine[activity_num]
            activity_r = None
            id += 1
            
            # ECKG
            
            activity_filepath = "./dataset/kg/vhakg_event/" + activity.replace("http://kgrc4si.home.kg/virtualhome2kg/instance/", "") + ".ttl"
            with open(activity_filepath, 'r') as f:
                activity_data = f.read()
                activity_data = updateEKGURI(activity_data, activity, id)

                g.parse(data=activity_data, format="ttl")
                g.bind("vh2kg", vh2kg)
                g.bind("time", time)
                g.bind("xsd", rdflib.XSD)
                g.bind("rdf", rdflib.RDF)
                g.bind("ho", ho)
                g.bind("ex", ex)

            event_and_duration_list = get_events_with_duration_from_activity(g, activity + "-" + str(id))
            activity_time = current_time
            for event_and_duration in event_and_duration_list:
                event = event_and_duration.event
                duration = event_and_duration.duration
                event_r = rdflib.URIRef(event)
                time_interval_r = ex["interval_" + event.replace(ex, "")]
                beginning_time_instant_r = ex["bt_" + event.replace(ex, "")]
                end_time_instant_r = ex["et_" + event.replace(ex, "")]
                # time_interval_r = rdflib.URIRef(str(ex) + str(i) + "/ti_" + event.fragment)
                # beginning_time_instant_r = rdflib.URIRef(str(ex)+ str(i) + "/bt_" + event.fragment)
                # end_time_instant_r = rdflib.URIRef(str(ex) + str(i) + "/et_" + event.fragment)
                g.add((time_interval_r, time.hasBeginning, beginning_time_instant_r))
                g.add((time_interval_r, time.hasEnd, end_time_instant_r))
                g.add((beginning_time_instant_r, time.inXSDDateTime, rdflib.Literal(activity_time.strftime("%Y-%m-%dT%H:%M:%S"), datatype=rdflib.XSD.dateTime)))
                # update activity_time
                activity_time = activity_time + datetime.timedelta(seconds=float(duration))
                g.add((end_time_instant_r, time.inXSDDateTime, rdflib.Literal(activity_time.strftime("%Y-%m-%dT%H:%M:%S"), datatype=rdflib.XSD.dateTime)))
                g.add((event_r, vh2kg.time, time_interval_r))
            
            if activity_num < len(routine) - 1:
                activity_r = rdflib.URIRef(activity + "-" + str(id))
                if (activity_r, vh2kg.activityNumber, None) not in g:
                    g.add((activity_r, vh2kg.activityNumber, rdflib.Literal(activity_num)))
                next_activity = routine[activity_num + 1]
                next_activity_r = rdflib.URIRef(next_activity + "-" + str(id+1))
                g.add((activity_r, vh2kg.nextActivity, next_activity_r))
                g.add((episode_r, vh2kg.hasActivity, activity_r))
            else:
                if (activity_r, vh2kg.activityNumber, None) not in g:
                    g.add((activity_r, vh2kg.activityNumber, rdflib.Literal(activity_num)))
                    g.add((episode_r, vh2kg.hasActivity, activity_r))

            # MMKG

            mmkg_directory = "./dataset/kg/vhakg_video_base64"
            for camera in range(5):
                # print(activity)
                tmp_filepath = mmkg_directory + "/*/*/vhakg_" + activity.replace("http://kgrc4si.home.kg/virtualhome2kg/instance/", "").capitalize() + "_camera" + str(camera) + "_2dbbox.ttl"
                tmp_filepath = fixFileName(tmp_filepath)
                mmkg_files = glob.glob(tmp_filepath, recursive=True)
                print(tmp_filepath)
                mmkg_filepath = [filepath for filepath in mmkg_files][0]
                with open(mmkg_filepath, 'r') as f:
                    mmkg_data = f.read()
                    mmkg_data = updateMMKGURI(mmkg_data, activity, id)
                    g.parse(data=mmkg_data, format="ttl")
                    g.bind("mssn", mssn)
                    g.bind("schema", schema)
                    g.bind("sosa", sosa)
                    

            current_time = current_time + datetime.timedelta(hours=1)
        
        exportEpisodeRDF(g, SCENE, episode_num)
        current_time = current_time.replace(hour=5, minute=0, second=0)
        current_time = current_time + datetime.timedelta(days=1)
        print(current_time)
    return g


# Main Execution
if __name__ == "__main__":
    # Data processing
    weekdays = []
    holidays = []
    for x in cs_results:
        weekdays.append(x[0:18])
        holidays.append(x[18:36])
    weekdays = convert_name(weekdays)
    holidays = convert_name(holidays)

    # Time-based sequence creation
    weekdays_morning = []
    weekdays_afternoon = []
    weekdays_evening = []
    holidays_morning = []
    holidays_afternoon = []
    holidays_evening = []
    for x in weekdays:
       weekdays_morning.append(add_start_end(x[0:6]))
       weekdays_afternoon.append(add_start_end(x[6:12]))
       weekdays_evening.append(add_start_end(x[12:18]))

    for x in holidays:
       holidays_morning.append(add_start_end(x[0:6]))
       holidays_afternoon.append(add_start_end(x[6:12]))
       holidays_evening.append(add_start_end(x[12:18]))

    # Create sequence list
    sequence_list = []
    for x in weekdays:
        sequence_list.append(add_start_end(x))
    for x in holidays:
        sequence_list.append(add_start_end(x))

    # Markov chain processing
    ngram = create_ngram(sequence_list)
    transition_probability = create_transition_probability(ngram)
    routine_list = []
    i = 0
    while i < EPISODE_NUM:
        mc = markov_chain(transition_probability)
        if len(mc) == 18:
            if mc not in routine_list:
                routine_list.append(mc)
                i += 1

    # RDF graph initialization
    rdf_g = rdflib.Graph()
    rdf_g.parse("data/vh2kg_schema_v2.0.0.ttl", format="ttl")

    # Ontology processing
    new_routine_list = []
    for routine in routine_list:
        new_routine = []
        for activity in routine:
            binding = get_activity_from_ontology(activity, SCENE)
            if binding is not None:
                new_routine.append(binding["activity"]["value"])
        new_routine_list.append(new_routine)

    # Export and create RDF
    export(new_routine_list, SCENE)
    g = create_episode_rdf(new_routine_list, INIT_TIME)