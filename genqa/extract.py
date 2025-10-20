import random
import math
from SPARQLWrapper import SPARQLWrapper, JSON
import datetime
import spacy
import en_core_web_sm
nlp = en_core_web_sm.load()
import pyinflect
import re
import os
import json
from openai import OpenAI
import textwrap

class Extractor:
    def __init__(self, repository=None, scene=None):
        self.scene = scene
        self.repository = repository
        self.action_object_pair = self.getActionObjectPair()
        self.min_max_pos3D = self.getMinMaxPos3D()
        self.spatial_relations = self.getSpatialRelations()
        self.prefix = """
            PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
            PREFIX mssn: <http://mssn.sigappfr.org/mssn/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
            PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
            PREFIX x3do: <https://www.web3d.org/specifications/X3dOntology4.0#>
            PREFIX ac: <http://kgrc4si.home.kg/virtualhome2kg/ontology/action/>
            PREFIX sosa: <http://www.w3.org/ns/sosa/>
            PREFIX time: <http://www.w3.org/2006/time#>
        """
        self.vh2kg = "http://kgrc4si.home.kg/virtualhome2kg/ontology/"
        self.ac = "http://kgrc4si.home.kg/virtualhome2kg/ontology/action/"
        self.ex = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
        print("initialized")

    def getActionMetadataValue(self, query_pattern_Action_type):
        value = None
        queryString =f"""
            {self.prefix}
            select distinct ?action where {{
                ?activity a ?activityClass ;
                    vh2kg:virtualHome ex:{self.scene} ;
                    vh2kg:hasEvent ?event .
                ?event vh2kg:action ?action .
            }}
        """
        sparql = SPARQLWrapper(self.repository)
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = random.choice(bindings)["action"]["value"]
                value = value.replace("http://kgrc4si.home.kg/virtualhome2kg/ontology/action/", "")
        except  Exception as e:
            print(e.args)
        return value

    def getObjectMetadataValue(self, query_pattern_Object_type=None, query_pattern_Action_value=None):
        value = None
        if query_pattern_Object_type == "None":
            print("query_pattern_Action_value", query_pattern_Action_value)
            if query_pattern_Action_value is None:
                tmp_object_candidate =  sum(list(self.action_object_pair.values()), [])
                # print("tmp_object_candidate", tmp_object_candidate)
                value = random.choice(tmp_object_candidate)
            else:
                if (self.ac + query_pattern_Action_value) in self.action_object_pair:
                    tmp_object_candidate = self.action_object_pair[self.ac + query_pattern_Action_value]
                    tmp_object = random.choice(tmp_object_candidate)
                    value = tmp_object
            return value
        elif query_pattern_Object_type == "Type":
            # Actionが選択されている場合はその値を使って絞り込む
            queryString = f"""
                {self.prefix}
                select distinct ?result where {{
                    ?activity a ?activityClass ;
                        vh2kg:virtualHome ex:{self.scene} ;
                        vh2kg:hasEvent ?event .
                    {'?event vh2kg:action ac:' + query_pattern_Action_value + ' .' if query_pattern_Action_value is not None else ''}
                    ?event vh2kg:mainObject ?object .
                    ?object a ?result .
                }}
            """
        elif query_pattern_Object_type == "Class":
            # Actionが選択されている場合はその値を使って絞り込む
            queryString = f"""
                {self.prefix}
                select distinct ?result where {{
                    ?activity a ?activityClass ;
                        vh2kg:virtualHome ex:{self.scene} ;
                        vh2kg:hasEvent ?event .
                    {'?event vh2kg:action ac:' + query_pattern_Action_value + ' .' if query_pattern_Action_value is not None else ''}
                    ?event vh2kg:mainObject ?object .
                    ?object a ?type .
                    ?type rdfs:subClassOf ?result .
                }}
            """
        elif query_pattern_Object_type == "State":
            # Actionが選択されている場合はその値を使って絞り込む
            queryString = f"""
                {self.prefix}
                select distinct ?result where {{
                    {'?event vh2kg:action ac:' + query_pattern_Action_value + ' . ?event vh2kg:mainObject ?object .' if query_pattern_Action_value is not None else ''}
                    ?state vh2kg:isStateOf ?object .
                    ?state a vh2kg:State ;
                        vh2kg:state ?result .
                    filter (?result != vh2kg:SITTING)
                }}
            """
        elif query_pattern_Object_type == "Attribute":
            queryString = f"""
                {self.prefix}
                select distinct ?result where {{
                    ?activity a ?activityClass ;
                        vh2kg:virtualHome ex:{self.scene} ;
                        vh2kg:hasEvent ?event .
                    {'?event vh2kg:action ac:' + query_pattern_Action_value + ' .' if query_pattern_Action_value is not None else ''}
                    ?event vh2kg:mainObject ?object .
                    ?object vh2kg:attribute ?result .
                }}
            """
        elif query_pattern_Object_type == "Affordance":
            # TODO: Implement this query
            print("skip")
        elif query_pattern_Object_type == "Size":
            # サイズと演算子を返す
            tmp_size = round(random.uniform(0, 1), 2)
            size_operator = random.choice(["<", ">", "<=", ">="])
            axis = random.choice(["x", "y", "z"])
            return (tmp_size, size_operator, axis)
        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = random.choice(bindings)["result"]["value"]
                value = value.replace("http://kgrc4si.home.kg/virtualhome2kg/instance/", "")
                value = value.replace("http://kgrc4si.home.kg/virtualhome2kg/ontology/", "")
        except  Exception as e:
            print("Failed to get object metadata value")
            print(e.args)
        return value

    def getMinMaxTime(self):
        queryString = f"""
            {self.prefix}
            select (min(?begin) as ?min) (max(?end) as ?max) where {{
                ?s vh2kg:time/time:hasEnd/time:inXSDDateTime ?end ;
                    vh2kg:time/time:hasBeginning/time:inXSDDateTime ?begin .
            }}
        """
        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        min_time = None
        max_time = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                min_time = bindings[0]["min"]["value"]
                max_time = bindings[0]["max"]["value"]
        except  Exception as e:
            print(e.args)
        return min_time, max_time 

    def getActionObjectPair(self):
        results = {}
        queryString = """
            PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
            select distinct ?action ?object where {
                ?event vh2kg:action ?action ;
                    vh2kg:mainObject ?object .
            }
        """
        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            for result in bindings:
                action = result["action"]["value"]
                object = result["object"]["value"]
                if action not in results:
                    results[action] = [object]
                else:
                    results[action].append(object)
        except  Exception as e:
            print(e.args)
        return results

    def getTimeMetadataValue(self, query_pattern_Time_type):
        value = None
        
        if query_pattern_Time_type == "Instant":
            min_time, max_time = self.getMinMaxTime()
            start_date = datetime.datetime.strptime(min_time, "%Y-%m-%dT%H:%M:%S")
            end_date = datetime.datetime.strptime(max_time, "%Y-%m-%dT%H:%M:%S")

            random_date = start_date + datetime.timedelta(days=random.randint(0, (end_date - start_date).days))
            random_time = datetime.time(random.randint(5, 22), random.randint(0, 1), 0) #動画は平均1分なので分数は0か1

            random_datetime = datetime.datetime.combine(random_date, random_time)
            random_datetime_formatted = random_datetime.strftime("%Y-%m-%dT%H:%M:%S")
            value = random_datetime_formatted
            
        elif query_pattern_Time_type == "Interval":
            # ランダムに時刻を生成
            min_time, max_time = self.getMinMaxTime()
            start_date = datetime.datetime.strptime(min_time, "%Y-%m-%dT%H:%M:%S")
            end_date = datetime.datetime.strptime(max_time, "%Y-%m-%dT%H:%M:%S")

            random_date1 = start_date + datetime.timedelta(days=random.randint(0, (end_date - start_date).days))
            random_time1 = datetime.time(random.randint(0, 23), random.randint(0, 59), 0)
            random_date2 = start_date + datetime.timedelta(days=random.randint(0, (end_date - start_date).days))
            random_time2 = datetime.time(random.randint(0, 23), random.randint(0, 59), 0)

            random_datetime1 = datetime.datetime.combine(random_date1, random_time1)
            random_datetime_formatted1 = random_datetime1.strftime("%Y-%m-%dT%H:%M:%S")
            random_datetime2 = datetime.datetime.combine(random_date2, random_time2)
            random_datetime_formatted2 = random_datetime2.strftime("%Y-%m-%dT%H:%M:%S")

            if random_datetime1 < random_datetime2:
                value = (random_datetime_formatted1, random_datetime_formatted2)
            else:
                value = (random_datetime_formatted2, random_datetime_formatted1)
        elif query_pattern_Time_type == "Duration":
            # ランダムにdurationを選択
            value = random.randint(0,22)
        elif query_pattern_Time_type == "Previous" or query_pattern_Time_type == "Next":
            # TODO: 一旦アクティビティはpending
            tmp_action = self.getAction()
            if tmp_action in self.action_object_pair:
                tmp_object_candidate = self.action_object_pair[tmp_action]
                tmp_object = random.choice(tmp_object_candidate)
                plus = random.choice(["", "+"])
                value = (tmp_action, tmp_object, plus)
            else:
                # tmp_action does not have object (e.g., stand)
                plus = random.choice(["", "+"])
                value = (tmp_action, None, plus)

        else:
            value = None

        return value


    def getPlaces(self, query_pattern_Action_value):
        places = None
        
        # pending: walkのfrom,toを考慮
        queryString = ""
        if query_pattern_Action_value is None:
            queryString = """
                PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
                select distinct ?place where {
                    ?s vh2kg:place ?place .
                }
            """
        else:
            queryString = f"""
                PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
                select distinct ?place where {{
                    ?s vh2kg:place ?place .
                    ?s vh2kg:action <{self.ac}{query_pattern_Action_value}> .
                }}
            """
        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                places = [result["place"]["value"] for result in bindings]
        except  Exception as e:
            print(e.args)
        return places

    def getMinMaxX(self):
        # prefix = """
        #     PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
        #     PREFIX x3do: <https://www.web3d.org/specifications/X3dOntology4.0#>
        # """
        # queryString = """
        #     {}
        #     select distinct (min(?x) AS ?min_x) (max(?x) AS ?max_x) where {{
        #         ?shape a x3do:Shape .
        #         ?shape x3do:bboxCenter ?bboxValue .
        #         ?bboxValue rdf:first ?x
        #     }}
        # """.format(prefix)

        # sparql = SPARQLWrapper("http://localhost:7200/repositories/vhakg-episode-" + scene)
        # sparql.addParameter('infer', 'false')
        # sparql.setQuery(queryString)
        # sparql.setReturnFormat(JSON)
        # value = None
        # try :
        #     json = sparql.query().convert()
        #     bindings = json['results']['bindings']
        #     if len(bindings) > 0:
        #         min_x = float(bindings[0]["min_x"]["value"])
        #         max_x = float(bindings[0]["max_x"]["value"])
        #         value = (min_x, max_x)
        # except  Exception as e:
        #     print(e.args)

        # # 時間がかかるため事前に取得した値をセット
        value = (-1.135993e+01, 8.639066e+00)
        return value

    def getMinMaxY(self):
        # prefix = """
        #     PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
        #     PREFIX x3do: <https://www.web3d.org/specifications/X3dOntology4.0#>
        # """
        # queryString = """
        #     {}
        #     select distinct (min(?y) AS ?min_y) (max(?y) AS ?max_y) where {{
        #         ?shape a x3do:Shape .
        #         ?shape x3do:bboxCenter ?bboxValue .
        #         ?bboxValue rdf:rest/rdf:first ?y
        #     }}
        # """.format(prefix)

        # sparql = SPARQLWrapper("http://localhost:7200/repositories/vhakg-episode-" + scene)
        # sparql.addParameter('infer', 'false')
        # sparql.setQuery(queryString)
        # sparql.setReturnFormat(JSON)
        # value = None
        # try :
        #     json = sparql.query().convert()
        #     bindings = json['results']['bindings']
        #     if len(bindings) > 0:
        #         min_y = float(bindings[0]["min_y"]["value"])
        #         max_y = float(bindings[0]["max_y"]["value"])
        #         value = (min_y, max_y)
        # except  Exception as e:
        #     print(e.args)

        # # 時間がかかるため事前に取得した値をセット
        value = (-3e-03, 2.5e+00)
        return value


    def getMinMaxZ(self):
        # prefix = """
        #     PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
        #     PREFIX x3do: <https://www.web3d.org/specifications/X3dOntology4.0#>
        # """
        # queryString = """
        #     {}
        #     select distinct (min(?z) AS ?min_z) (max(?z) AS ?max_z) where {{
        #         ?shape a x3do:Shape .
        #         ?shape x3do:bboxCenter ?bboxValue .
        #         ?bboxValue rdf:rest/rdf:rest/rdf:first ?z
        #     }}
        # """.format(prefix)

        # sparql = SPARQLWrapper("http://localhost:7200/repositories/vhakg-episode-" + scene)
        # sparql.addParameter('infer', 'false')
        # sparql.setQuery(queryString)
        # sparql.setReturnFormat(JSON)
        # value = None
        # try :
        #     json = sparql.query().convert()
        #     bindings = json['results']['bindings']
        #     if len(bindings) > 0:
        #         min_z = float(bindings[0]["min_z"]["value"])
        #         max_z = float(bindings[0]["max_z"]["value"])
        #         value = (min_z, max_z)
        # except  Exception as e:
        #     print(e.args)

        # # 時間がかかるため事前に取得した値をセット
        value = (-1.16982e+01, 3.222999e+00)
        return value


    def getMinMaxPos3D(self):
        min_max_x = self.getMinMaxX()
        min_x = min_max_x[0]
        max_x = min_max_x[1]
        min_max_y = self.getMinMaxY()
        min_y = min_max_y[0]
        max_y = min_max_y[1]
        min_max_z = self.getMinMaxZ()
        min_z = min_max_z[0]
        max_z = min_max_z[1]
        return (min_x, max_x, min_y, max_y, min_z, max_z)


    def getSpatialRelations(self):
        prefix = """
            PREFIX vh2kg: <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
            PREFIX x3do: <https://www.web3d.org/specifications/X3dOntology4.0#>
        """
        queryString = f"""
            {prefix}
            select distinct ?relation where {{
                ?shape1 a x3do:Shape .
                ?shape2 a x3do:Shape .
                ?shape1 ?relation ?shape2 .
            }}
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["relation"]["value"] for result in bindings]
        except  Exception as e:
            print(e.args)
        return value


    def get2Dbbox(self):
        # return an entity of 2D bounding box
        queryString = f"""
            {self.prefix}
            SELECT DISTINCT ?s WHERE {{
                {{
                    select distinct ?object where {{
                        ?object rdf:type/rdfs:subClassOf* vh2kg:Object .
                        BIND(RAND() AS ?rand)
                    }} order by ?rand limit 1
                }}
                ?s a mssn:BoundingBoxDescriptor ;
                vh2kg:is2DbboxOf ?object .
                BIND(RAND() AS ?rand2)
            }} order by ?rand2 limit 1
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["s"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value


    def getSpaceMetadataValue(self, query_pattern_Space_type, query_pattern_Action_value):
        value = None
        object2 = None
        object2_name = None

        if query_pattern_Space_type == "Place":
            try:
                candidates = self.getPlaces(query_pattern_Action_value)
                if candidates is None:
                    return None
                value = random.choice(candidates)
            except Exception as e:
                print(e.args)
                assert False
        elif query_pattern_Space_type == "Pos3D":
            min_x, max_x, min_y, max_y, min_z, max_z = self.min_max_pos3D
            x = round(random.uniform(min_x, max_x), 2)
            y = round(random.uniform(min_y, max_y), 2)
            z = round(random.uniform(min_z, max_z), 2)
            value = (x, y, z)       
        elif query_pattern_Space_type == "Relation":
            relation = random.choice(self.spatial_relations)
            relation = relation.replace(self.vh2kg, "")
            # 選択したrelationを持つオブジェクトを検索
            shape2 = self.getObjectRelationValue(relation=relation, action=query_pattern_Action_value)
            object2_name = self.getObjectNameFromShape(shape2)
            value = (relation, object2_name)
        elif query_pattern_Space_type == "Pos2D":
            # あるオブジェクトがカメラに映っているかを検索するためにオブジェクトのbboxを取得
            while True:
                value = self.get2Dbbox()
                if value is not None:
                    break
        else:
            value = None
            assert False, "query_pattern_Space_type is not defined"
        return value

    def getVideoMetadataValue(self, query_pattern_Video_type):
        return False


    # def getQueryPatternOTypeTriples(self, query_pattern_Object_type, query_pattern_Object_value):
    #     result = None
    #     if query_pattern_Object_type == "None":
    #         object_name = self.getObjectName(query_pattern_Object_value)
    #         result = f"""?event vh2kg:mainObject ?object . ?object rdfs:label "{object_name}" . """
    #     elif query_pattern_Object_type == "Type":
    #         result = f"""
    #             ?event vh2kg:mainObject ?object .
    #             ?object a {query_pattern_Object_value} .
    #             """
    #     elif query_pattern_Object_type == "Class":
    #         result = f"""
    #             ?event vh2kg:mainObject ?object .
    #             ?object a ?objectType .
    #             ?objectType rdfs:subClassOf <{query_pattern_Object_value}> .
    #         """
    #     elif query_pattern_Object_type == "State":
    #         result = f"""
    #             ?state vh2kg:isStateOf ?object ;
    #                 vh2kg:state <{query_pattern_Object_value}> .
    #         """
    #     return result


    def getObjectRelationValue(self, relation=None, action=None):
        # Random choicing a tail of an object relation triple.
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?shape2 WHERE {{
            ?shape1 vh2kg:inside ?shape2 .
            BIND(RAND() AS ?rand)
        }} order by ?rand limit 1 """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["shape2"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value


    def getObjectShape(self):
        # Random choicing a shape of an object.
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?shape WHERE {{ 
        ?shape a x3do:Shape .
        BIND(RAND() AS ?rand)
        }} order by ?rand limit 1
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["shape"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value


    def getObjectRelatedToGivenObject(self, object_uri):
        # Random choicing a object related to the given object.
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?object2 WHERE {{
            ?state vh2kg:isStateOf <{object_uri}> .
            ?state vh2kg:bbox ?bbox .
            ?bbox ?relation ?bbox2 .
            ?state2 vh2kg:bbox ?bbox2 ;
                    vh2kg:isStateOf ?object2 .
            BIND(RAND() AS ?rand)
        }} order by ?rand limit 1
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["object2"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value


    def getObjectPlace(self, shape):
        # Identify the location of a given object' shape resource.
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?place WHERE {{ 
            <{self.shape}> vh2kg:inside ?placeShape .
            ?placeState vh2kg:bbox ??placeShape ;
                        vh2kg:isStateOf ?place . 
            ?place rdf:type/rdfs:subClassOf* vh2kg:Room .
        }} limit 1
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["place"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value


    def getObject(self):
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?object WHERE {{ 
            ?object rdf:type/rdfs:subClassOf* vh2kg:Object .
            BIND(RAND() AS ?rand)
        }} order by ?rand limit 1
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["object"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value


    def getObjectNameFromShape(self, shape):
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?name WHERE {{ 
            ?state vh2kg:bbox <{shape}> .
            ?state vh2kg:isStateOf ?object .
            ?object rdfs:label ?name .
        }}
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["name"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value

    def getObjectName(self, object_uri):
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?name WHERE {{ 
            <{object_uri}> rdfs:label ?name .
        }}
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["name"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value
    
    def getObjectNameFrom2Dbbox(self, bbox_uri):
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?name WHERE {{ 
            <{bbox_uri}> vh2kg:is2DbboxOf ?object .
            ?object rdfs:label ?name .
        }}
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        value = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                value = [result["name"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return value


    def getAction(self):
        queryString = f"""
        {self.prefix}
        SELECT DISTINCT ?action WHERE {{ 
            ?event vh2kg:action ?action .
            ?action rdf:type vh2kg:Action .
            bind(rand() as ?rand)
        }} order by ?rand limit 1
        """

        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        result = None
        try :
            json = sparql.query().convert()
            bindings = json['results']['bindings']
            if len(bindings) > 0:
                result = [result["action"]["value"] for result in bindings][0]
        except  Exception as e:
            print(e.args)
        return result

    def to_progressive(self, verb):
        # 例外処理: 特殊な動詞の変換
        exceptions = {
            "be": "being",
            "see": "seeing",
            "flee": "fleeing",
            "knee": "kneeing",
        }
        if verb in exceptions:
            return exceptions[verb]
        
        # ルール1: 子音+母音+子音で終わる短い動詞（最後の子音を重ねる）
        if len(verb) > 2 and verb[-1] not in "aeiou" and verb[-2] in "aeiou" and verb[-3] not in "aeiou":
            return verb + verb[-1] + "ing"
        
        # ルール2: "e" で終わる動詞（"e" を削除して "ing" を追加）
        elif verb.endswith("e"):
            return verb[:-1] + "ing"
        
        # ルール3: 一般的な動詞（そのまま "ing" を追加）
        else:
            return verb + "ing"

    def to_past(self, action):
        if action == "legopp":
            return "operated with feet"
        action_dep = nlp(action)
        action_past = action.replace(action_dep[0].text, action_dep[0]._.inflect("VBD"))
        return action_past
    

    def createSpatialQueryPattern(self, query_pattern_Space_type=None, query_pattern_Space_value=None, query_pattern_Space_operator=None, query_pattern_Action_value=None, query_pattern_Action_operator=None, query_pattern_Time_value=None, query_pattern_Time_operator=None, query_pattern_Object_type=None, query_pattern_Object_value=None):
        query_pattern_Space_triple = ""
        sparql_header = "SELECT DISTINCT ?answer"
        text_header = ""
        filter = ""
        if query_pattern_Space_type == "Place":
            if query_pattern_Space_value is None:
                print("Skip: Place value is None.")
                return ""
            s_value_name = self.getObjectName(query_pattern_Space_value)
            if query_pattern_Action_value == "walk":
                is_from_to = True
            else:
                is_from_to = False
            if is_from_to:
                query_pattern_Space_triple = f"""
                ?event vh2kg:from ?from ; vh2kg:to ?to .
                ?to rdfs:label "{s_value_name}" .
                """
            else:
                query_pattern_Space_triple = f"""
                ?event vh2kg:place ?place .
                ?place rdfs:label "{s_value_name}" .
                """
        elif query_pattern_Space_type == "Pos3D":
            pos3d_operator = query_pattern_Space_operator
            if pos3d_operator == "x+":
                filter = f"""FILTER("{query_pattern_Space_value[0]}"^^xsd:double < ?pos_x)"""
            elif pos3d_operator == "x-":
                filter = f"""FILTER("{query_pattern_Space_value[0]}"^^xsd:double > ?pos_x)"""
            elif pos3d_operator == "y+":
                filter = f"""FILTER("{query_pattern_Space_value[1]}"^^xsd:double < ?pos_y)"""
            elif pos3d_operator == "y-":
                filter = f"""FILTER("{query_pattern_Space_value[1]}"^^xsd:double > ?pos_y)"""
            elif pos3d_operator == "z+":
                filter = f"""FILTER("{query_pattern_Space_value[2]}"^^xsd:double < ?pos_z)"""
            elif pos3d_operator == "z-":
                filter = f"""FILTER("{query_pattern_Space_value[2]}"^^xsd:double > ?pos_z)"""
            
            if pos3d_operator == "x+" or pos3d_operator == "x-":
                query_pattern_Space_triple = f"""
                    ?state vh2kg:isStateOf ?object .
                    ?state vh2kg:bbox ?shape .
                    ?shape x3do:bboxCenter ?pos3d .
                    ?pos3d rdf:first ?pos_x .
                    {filter}
                """
            elif pos3d_operator == "y+" or pos3d_operator == "y-":
                query_pattern_Space_triple = f"""
                    ?state vh2kg:isStateOf ?object .
                    ?state vh2kg:bbox ?shape .
                    ?shape x3do:bboxCenter ?pos3d .
                    ?pos3d rdf:rest/rdf:first ?pos_y .
                    {filter}
                """
            elif pos3d_operator == "z+" or pos3d_operator == "z-":
                query_pattern_Space_triple = f"""
                    ?state vh2kg:isStateOf ?object .
                    ?state vh2kg:bbox ?shape .
                    ?shape x3do:bboxCenter ?pos3d .
                    ?pos3d rdf:rest/rdf:rest/rdf:first ?pos_z .
                    {filter}
                """
            else:
                print("Pos3D operator error")
                print(query_pattern_Space_operator)
                assert False
            
            if query_pattern_Object_value is None:
                query_pattern_Space_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    {query_pattern_Space_triple}
                    """
        elif query_pattern_Space_type == "Relation":
            relation = query_pattern_Space_value[0]
            object2_name = query_pattern_Space_value[1]
            query_pattern_Space_triple = f"""
                ?event vh2kg:situationAfterEvent ?situation .
                ?state vh2kg:partOf ?situation .
                ?state vh2kg:isStateOf ?object .
                ?state vh2kg:bbox ?shape .
                ?shape vh2kg:{relation} ?shape2 .
                ?state2 vh2kg:bbox ?shape2 ;
                    vh2kg:isStateOf ?object2 .
                ?object2 rdfs:label "{object2_name}" .
            """
            if query_pattern_Object_value is None:
                query_pattern_Space_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    {query_pattern_Space_triple}
                """
        # elif query_pattern_Space_type == "Pos2D":
        #     # print("Pos2D", query_pattern_Space_value)
            
        #     # # 2D座標で位置関係を検索するのは時間がかかりすぎて無理かも
        #     # if query_pattern_Space_operator == "above":
        #     #     filter = "FILTER(?lt_y > ?rb_y2)"
        #     # elif query_pattern_Space_operator == "below":
        #     #     filter = "FILTER(?rb_y < ?lt_y2)"
        #     # elif query_pattern_Space_operator == "left":
        #     #     filter = "FILTER(?lt_x > ?rb_x2)"
        #     # elif query_pattern_Space_operator == "right":
        #     #     filter = "FILTER(?rb_x < ?lt_x2)"

        #     object_name = self.getObjectNameFrom2Dbbox(query_pattern_Space_value)
        #     query_pattern_Space_triple = f"""
        #         ?md mssn:hasMediaSegment ?vs ;
        #             sosa:madeBySensor ex:camera2_{self.scene} .
        #         ?vs vh2kg:isVideoSegmentOf ?event ;
        #             mssn:hasMediaDescriptor ?frame .
        #         ?frame mssn:hasMediaDescriptor ?bbox2d .
        #         ?bbox2d vh2kg:is2DbboxOf ?visible_object ;
        #                 vh2kg:bbox-2d-value ?b1 .
        #         ?visible_object rdfs:label "{object_name}" .
        #         {filter}
        #     """
            
        else:
            print("Space")
            assert False
        return query_pattern_Space_triple
    
    def createTemporalQueryPattern(self, query_pattern_Time_type=None, query_pattern_Time_value=None, query_pattern_Time_operator=None, action_object_dict=None):
        query_pattern_Time_triple = ""
        sparql_footer = None
        if query_pattern_Time_type == "Instant":
            query_pattern_Time_triple = f"""
                ?event vh2kg:time ?time_interval .
                ?time_interval time:hasBeginning ?begin ;
                    time:hasEnd ?end .
                ?begin time:inXSDDateTime ?begin_time .
                ?end time:inXSDDateTime ?end_time .
                FILTER(?begin_time <= "{query_pattern_Time_value}"^^xsd:dateTime && "{query_pattern_Time_value}"^^xsd:dateTime <= ?end_time)
            """
        elif query_pattern_Time_type == "Interval":
            filter = ""
            if query_pattern_Time_operator == "< <":
                filter = f"""FILTER("{query_pattern_Time_value[0]}"^^xsd:dateTime < ?begin_time && ?end_time < "{query_pattern_Time_value[1]}"^^xsd:dateTime)"""
            elif query_pattern_Time_operator == "<= <":
                filter = f"""FILTER("{query_pattern_Time_value[0]}"^^xsd:dateTime <= ?begin_time && ?end_time < "{query_pattern_Time_value[1]}"^^xsd:dateTime)"""
            elif query_pattern_Time_operator == "< <=":
                filter = f"""FILTER("{query_pattern_Time_value[0]}"^^xsd:dateTime < ?begin_time && ?end_time <= "{query_pattern_Time_value[1]}"^^xsd:dateTime)"""
            elif query_pattern_Time_operator == "<= <=":
                filter = f"""FILTER("{query_pattern_Time_value[0]}"^^xsd:dateTime <= ?begin_time && ?end_time <= "{query_pattern_Time_value[1]}"^^xsd:dateTime)"""
            else:
                print("T operation error")
                print(query_pattern_Time_operator)
                assert False
            query_pattern_Time_triple = f"""
                ?event vh2kg:time ?time_interval .
                ?time_interval time:hasBeginning ?begin .
                ?begin time:inXSDDateTime ?begin_time .
                ?time_interval time:hasEnd ?end .
                ?end time:inXSDDateTime ?end_time .
                {filter}
            """
        elif query_pattern_Time_type == "Duration":
            filter = f"""FILTER(?duration {query_pattern_Time_operator} {query_pattern_Time_value})"""
            query_pattern_Time_triple = f"""
                ?event vh2kg:time ?time_duration .
                ?time_duration time:numericDuration ?duration .
                {filter}
            """
        elif query_pattern_Time_type == "Current":
            query_pattern_Time_triple = f"""
                ?event vh2kg:time ?time_interval .
                ?time_interval time:hasEnd ?end .
                ?end time:inXSDDateTime ?end_time .
            """
            sparql_footer = "order by desc(?end) limit 1"
        elif query_pattern_Time_type == "First":
            query_pattern_Time_triple = f"""
                ?event vh2kg:time ?time_interval .
                ?time_interval time:hasBeginning ?begin .
                ?begin time:inXSDDateTime ?begin_time .
            """
            sparql_footer = "order by asc(?begin_time) limit 1"
        elif query_pattern_Time_type == "Last":
            query_pattern_Time_triple  = f"""
                ?event vh2kg:time ?time_interval .
                ?time_interval time:hasEnd ?end .
                ?end time:inXSDDateTime ?end_time .
            """
            sparql_footer = "order by desc(?end_time) limit 1"
        elif query_pattern_Time_type == "Next":
            # prev_objectをprev_actionした"次"のeventを取得
            
            prev_action = query_pattern_Time_value[0]
            prev_object = query_pattern_Time_value[1]
            plus = query_pattern_Time_value[2]
            

            if prev_object is not None:
                prev_object_name = self.getObjectName(prev_object)
                query_pattern_Time_triple = f"""
                    {{
                        select distinct * where {{
                            ?prev_event vh2kg:nextEvent{plus} ?event .
                            ?prev_event vh2kg:action {prev_action.replace(self.ac, "ac:")} .
                            ?prev_event vh2kg:mainObject ?prev_object .
                            ?prev_object rdfs:label "{prev_object_name}" .
                            ?event vh2kg:eventNumber ?event_number .
                        }} order by asc(?event_number) limit 1
                    }}
                    """
            # objectが無いアクション（standなど）
            else:
                query_pattern_Time_triple = f"""
                    {{
                        select distinct * where {{
                            ?prev_event vh2kg:nextEvent{plus} ?event .
                            ?prev_event vh2kg:action {prev_action.replace(self.ac, "ac:")} .
                            ?event vh2kg:eventNumber ?event_number .
                        }} order by asc(?event_number) limit 1
                    }}
                    """
            
        elif query_pattern_Time_type == "Previous":
            # next_objectをnext_actionした"前"のeventを取得

            next_action = query_pattern_Time_value[0]
            next_object = query_pattern_Time_value[1]
            plus = query_pattern_Time_value[2]

            if next_action is not None:
                next_action = next_action.replace(self.ac, "ac:")

            if next_object is not None:
                next_object_name = self.getObjectName(next_object)
                query_pattern_Time_triple = f"""
                    {{
                        select distinct * where {{
                            ?event vh2kg:nextEvent{plus} ?next_event .
                            ?next_event vh2kg:action {next_action} .
                            ?next_event vh2kg:mainObject ?next_object .
                            ?next_object rdfs:label "{next_object_name}" .
                            ?event vh2kg:eventNumber ?event_number .
                        }} order by desc(?event_number) limit 1
                    }}
                    """
            # objectが無いアクション（standなど）
            else:
                query_pattern_Time_triple = f"""
                    {{
                        select distinct * where {{
                            ?event vh2kg:nextEvent{plus} ?next_event .
                            ?next_event vh2kg:action {next_action} .
                            ?event vh2kg:eventNumber ?event_number .
                        }} order by desc(?event_number) limit 1
                    }}
                    """
        else:
            print("T metadata error")
            assert False
        return query_pattern_Time_triple, sparql_footer

    def createObjectQueryPattern(self, query_pattern_Object_type=None, query_pattern_Object_value=None):
        # TODO: implement
        query_pattern_Object_triple = None
        if query_pattern_Object_type == "None":
            object_name = self.getObjectName(self.ex + query_pattern_Object_value)
            query_pattern_Object_triple = f"""?event vh2kg:mainObject ?object . ?object rdfs:label "{object_name}" . """
        elif query_pattern_Object_type == "Type":
            query_pattern_Object_triple = f"""
                ?event vh2kg:mainObject ?object .
                ?object a vh2kg:{query_pattern_Object_value} .
                """
        elif query_pattern_Object_type == "Class":
            query_pattern_Object_triple = f"""
                ?event vh2kg:mainObject ?object .
                ?object a ?objectType .
                ?objectType rdfs:subClassOf vh2kg:{query_pattern_Object_value} .
            """
        elif query_pattern_Object_type == "State":
            query_pattern_Object_triple = f"""
                ?event vh2kg:mainObject ?object .
                ?state vh2kg:isStateOf ?object ;
                    vh2kg:state vh2kg:{query_pattern_Object_value} .
            """
        elif query_pattern_Object_type == "Attribute":
            query_pattern_Object_triple = f"""
                ?event vh2kg:mainObject ?object .
                ?object vh2kg:attribute vh2kg:{query_pattern_Object_value} .
            """
        elif query_pattern_Object_type == "Size":
            size = query_pattern_Object_value[0]
            size_operator = query_pattern_Object_value[1]
            axis = query_pattern_Object_value[2]
            if axis == "x":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?state vh2kg:isStateOf ?object ;
                        vh2kg:bbox ?shape .
                    ?shape x3do:bboxSize ?size .
                    ?size rdf:first ?size_x .
                    filter(?size_x {size_operator} {size})
                """
            elif axis == "y":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?state vh2kg:isStateOf ?object ;
                        vh2kg:bbox ?shape .
                    ?shape x3do:bboxSize ?size .
                    ?size rdf:rest/rdf:first ?size_y .
                    filter(?size_y {size_operator} {size})
                """
            elif axis == "z":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?state vh2kg:isStateOf ?object ;
                        vh2kg:bbox ?shape .
                    ?shape x3do:bboxSize ?size .
                    ?size rdf:rest/rdf:rest/rdf:first ?size_z .
                    filter(?size_z {size_operator} {size})
                """
        return query_pattern_Object_triple

    def checkInitialPairs(self, selected_answer_type=None, query_pattern_Object_type=None, query_pattern_Object_value=None, query_pattern_Action_type=None, query_pattern_Action_value=None, query_pattern_Space_type=None, query_pattern_Space_value=None, query_pattern_Space_operator=None, query_pattern_Time_type=None, query_pattern_Time_value=None, query_pattern_Time_operator=None):
        result = False
        queryString = ""
        object_query_pattern = None
        action_query_pattern = None
        spatial_query_pattern = None
        temporal_query_pattern = None
        # 問う対象がSかTのとき
        if selected_answer_type == "Space" or selected_answer_type == "Time":
            if query_pattern_Action_value is None:
                print("Skip: A value is None.")
                return False, None, None, None, None
            action_query_pattern = "?event vh2kg:action ac:{} .".format(query_pattern_Action_value.replace("ac:", ""))
            # object_query_pattern = createObjectQueryPatter()
            object_query_pattern = ""
            if selected_answer_type == "Time": #Tを問う場合
                spatial_query_pattern = self.createSpatialQueryPattern(query_pattern_Space_type=query_pattern_Space_type, query_pattern_Space_value=query_pattern_Space_value, query_pattern_Space_operator=query_pattern_Space_operator, query_pattern_Action_value=query_pattern_Action_value)
                if query_pattern_Object_value is not None:
                    object_query_pattern = self.createObjectQueryPattern(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Object_value=query_pattern_Object_value)
                queryString = f"""
                    {self.prefix}
                    ASK {{
                        {{ select * where {{
                        {action_query_pattern}
                        {object_query_pattern}
                        }} }}
                        {spatial_query_pattern}
                    }}
                """
            else: #Sを問う場合
                temporal_query_pattern, sparql_footer = self.createTemporalQueryPattern(query_pattern_Time_type=query_pattern_Time_type, query_pattern_Time_value=query_pattern_Time_value, query_pattern_Time_operator=query_pattern_Time_operator)
                if query_pattern_Object_value is not None:
                    object_query_pattern = self.createObjectQueryPattern(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Object_value=query_pattern_Object_value)
                queryString = f"""
                    {self.prefix}
                    ASK {{
                        {action_query_pattern}
                        {object_query_pattern}
                        {temporal_query_pattern}
                    }}
                """
        # 問う対象がOかAのとき
        elif selected_answer_type == "Object" or selected_answer_type == "Action":
            #Aを問う場合
            if selected_answer_type == "Action": 
                if query_pattern_Object_type == "Size" and query_pattern_Space_type == "Pos3D":
                    # Objectがサイズ指定、空間が座標指定の場合クエリが制限実行時間内に終了しないためスキップ
                    print("Skip: Object is Size and Space is Pos3D.")
                    return False, object_query_pattern, action_query_pattern, spatial_query_pattern, temporal_query_pattern
                spatial_query_pattern = self.createSpatialQueryPattern(query_pattern_Space_type=query_pattern_Space_type, query_pattern_Space_value=query_pattern_Space_value, query_pattern_Space_operator=query_pattern_Space_operator, query_pattern_Action_value=query_pattern_Action_value, query_pattern_Object_type=query_pattern_Object_type, query_pattern_Object_value=query_pattern_Object_value)
                temporal_query_pattern, sparql_footer = self.createTemporalQueryPattern(query_pattern_Time_type=query_pattern_Time_type, query_pattern_Time_value=query_pattern_Time_value, query_pattern_Time_operator=query_pattern_Time_operator)
                object_query_pattern = self.createObjectQueryPattern(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Object_value=query_pattern_Object_value)
                queryString = f"""
                    {self.prefix}
                    ASK {{
                        {object_query_pattern}
                        {spatial_query_pattern}
                        {temporal_query_pattern}
                    }}
                """
            #Oを問う場合
            else:
                if query_pattern_Action_value is None:
                    print("Skip: A value is None.")
                    return False, None, None, None, None
                action_query_pattern = "?event vh2kg:action ac:{} .".format(query_pattern_Action_value.replace("ac:", ""))
                spatial_query_pattern = self.createSpatialQueryPattern(query_pattern_Space_type=query_pattern_Space_type, query_pattern_Space_value=query_pattern_Space_value, query_pattern_Space_operator=query_pattern_Space_operator, query_pattern_Action_value=query_pattern_Action_value)
                temporal_query_pattern, sparql_footer = self.createTemporalQueryPattern(query_pattern_Time_type=query_pattern_Time_type, query_pattern_Time_value=query_pattern_Time_value, query_pattern_Time_operator=query_pattern_Time_operator)
                queryString = f"""
                    {self.prefix}
                    ASK {{
                        {action_query_pattern}
                        {spatial_query_pattern}
                        {temporal_query_pattern}
                    }}
                """
        elif selected_answer_type == "Aggregation" or selected_answer_type == "Activity" or selected_answer_type == "Video": 
            action_query_pattern = ""
            object_query_pattern = ""
            spatial_query_pattern = ""
            temporal_query_pattern = ""
            if query_pattern_Action_value is not None:
                action_query_pattern = "?event vh2kg:action ac:{} .".format(query_pattern_Action_value.replace("ac:", ""))
            if query_pattern_Object_value is not None:
                object_query_pattern = self.createObjectQueryPattern(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Object_value=query_pattern_Object_value)
            if query_pattern_Space_value is not None:
                spatial_query_pattern = self.createSpatialQueryPattern(query_pattern_Space_type=query_pattern_Space_type, query_pattern_Space_value=query_pattern_Space_value, query_pattern_Space_operator=query_pattern_Space_operator, query_pattern_Action_value=query_pattern_Action_value)
            if query_pattern_Time_value is not None:
                temporal_query_pattern, sparql_footer = self.createTemporalQueryPattern(query_pattern_Time_type=query_pattern_Time_type, query_pattern_Time_value=query_pattern_Time_value, query_pattern_Time_operator=query_pattern_Time_operator)
            queryString = f"""
                {self.prefix}
                ASK {{
                    {{ select * where {{
                        {action_query_pattern}
                        {object_query_pattern}
                    }} }}
                    {spatial_query_pattern}
                    {temporal_query_pattern}
                }}
            """

        else:
            print("selected_answer_type error")
            assert False

        
        print("checkInitialPairs queryString:")
        print(queryString)
        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        try :
            json = sparql.query().convert()
            result = json["boolean"]
        except  Exception as e:
            print("checkInitialPairs error:")
            print(e.args)
        return result, object_query_pattern, action_query_pattern, spatial_query_pattern, temporal_query_pattern
    
    def getTemporalQualifierText(self, query_pattern_Time_type=None, query_pattern_Time_value=None, query_pattern_Time_operator=None):
        temporal_qualifier_en = ""
        if query_pattern_Time_type == "Instant":
            temporal_qualifier_en = f"at {query_pattern_Time_value}"
        elif query_pattern_Time_type == "Interval":
            if query_pattern_Time_operator == "< <":
                temporal_qualifier_ja = f"{query_pattern_Time_value[0]}より後で{query_pattern_Time_value[1]}より前に"
                temporal_qualifier_en = f"after {query_pattern_Time_value[0]} and before {query_pattern_Time_value[1]}"
            elif query_pattern_Time_operator == "<= <":
                temporal_qualifier_ja = f"{query_pattern_Time_value[0]}以降で{query_pattern_Time_value[1]}より前に"
                temporal_qualifier_en = f"after or at {query_pattern_Time_value[0]} and before {query_pattern_Time_value[1]}"
            elif query_pattern_Time_operator == "< <=":
                temporal_qualifier_ja = f"{query_pattern_Time_value[0]}より後で{query_pattern_Time_value[1]}以前に"
                temporal_qualifier_en = f"after {query_pattern_Time_value[0]} and before or at {query_pattern_Time_value[1]}"
            elif query_pattern_Time_operator == "<= <=":
                temporal_qualifier_ja = f"{query_pattern_Time_value[0]}から{query_pattern_Time_value[1]}までの間に"
                temporal_qualifier_en = f"from {query_pattern_Time_value[0]} to {query_pattern_Time_value[1]}"
        elif query_pattern_Time_type == "Duration":
            if query_pattern_Time_operator == "<":
                temporal_qualifier_ja = f"{query_pattern_Time_value}秒未満"
                temporal_qualifier_en = f"less than {query_pattern_Time_value} seconds"
            elif query_pattern_Time_operator == ">":
                temporal_qualifier_ja = f"{query_pattern_Time_value}秒より長い時間"
                temporal_qualifier_en = f"more than {query_pattern_Time_value} seconds"
            elif query_pattern_Time_operator == "<=":
                temporal_qualifier_ja = f"{query_pattern_Time_value}秒以上"
                temporal_qualifier_en = f"less than or equal to {query_pattern_Time_value} seconds"
            elif query_pattern_Time_operator == ">=":
                temporal_qualifier_ja = f"{query_pattern_Time_value}秒以下"
                temporal_qualifier_en = f"more than or equal to {query_pattern_Time_value} seconds"
        elif query_pattern_Time_type == "Current":
            temporal_qualifier_ja = "現在"
            temporal_qualifier_en = "currently"
        elif query_pattern_Time_type == "First":
            temporal_qualifier_ja = "最初に"
            temporal_qualifier_en = "firstly"
        elif query_pattern_Time_type == "Last":
            temporal_qualifier_ja = "最後に"
            temporal_qualifier_en = "lastly"
        elif query_pattern_Time_type == "Previous":
            next_action = query_pattern_Time_value[0]
            next_object = query_pattern_Time_value[1]
            plus = query_pattern_Time_value[2]
            if next_object is None:
                next_object = ""
            if next_action is None:
                next_action = ""
            if plus == "+":
                temporal_qualifier_ja = f"{next_object.replace(self.ex, "").replace("_" + self.scene, "")}を{next_action.replace(self.ac, "")}した以前に、"
                temporal_qualifier_en = f"before {self.to_progressive(next_action.replace(self.ac, ''))} the {next_object.replace(self.ex, '').replace('_' + self.scene, '')}"
            else:
                temporal_qualifier_ja = f"{next_object.replace(self.ex, "").replace("_" + self.scene, "")}を{next_action.replace(self.ac, "")}した直前に、"
                temporal_qualifier_en = f"just before {self.to_progressive(next_action.replace(self.ac, ''))} the {next_object.replace(self.ex, '').replace('_' + self.scene, '')}"
        elif query_pattern_Time_type == "Next":
            prev_action = query_pattern_Time_value[0]
            prev_object = query_pattern_Time_value[1]
            plus = query_pattern_Time_value[2]
            if prev_object is None:
                prev_object = ""
            if prev_action is None:
                prev_action = ""
            if plus == "+":
                temporal_qualifier_ja = f"{prev_object.replace(self.ex, "").replace("_" + self.scene, "")}を{prev_action.replace(self.ac, "")}した以後に、"
                temporal_qualifier_en = f"after {self.to_progressive(prev_action.replace(self.ac, ''))} the {prev_object.replace(self.ex, '').replace('_' + self.scene, '')}"
            else:
                temporal_qualifier_ja = f"{prev_object.replace(self.ex, "").replace("_" + self.scene, "")}を{prev_action.replace(self.ac, "")}した直後に、"
                temporal_qualifier_en = f"just after {self.to_progressive(prev_action.replace(self.ac, ''))} the {prev_object.replace(self.ex, '').replace('_' + self.scene, '')}"
        else:
            print("query_pattern_Time_type error:", query_pattern_Time_type)
            assert False
        if temporal_qualifier_ja is None:
            temporal_qualifier_ja = ""
        if temporal_qualifier_en is None:
            temporal_qualifier_en = ""
        return temporal_qualifier_ja, temporal_qualifier_en
    
    def getSpatialQualifierText(self, query_pattern_Space_type=None, query_pattern_Space_value=None, query_pattern_Space_operator=None):
        spatial_qualifier_ja = ""
        spatial_qualifier_en = ""
        if query_pattern_Space_type == "Place":
            place_name = self.getObjectName(query_pattern_Space_value)
            if place_name is None:
                return "", ""
            spatial_qualifier_ja = f"{place_name}"
            spatial_qualifier_en = f"{place_name}"
        elif query_pattern_Space_type == "Pos3D":
            if query_pattern_Space_operator == "x+":
                spatial_qualifier_ja = f"X座標が{query_pattern_Space_value[0]}より大きい位置"
                spatial_qualifier_en = f"at a position where the X coordinate is greater than {query_pattern_Space_value[0]}"
            elif query_pattern_Space_operator == "x-":
                spatial_qualifier_ja = f"X座標が{query_pattern_Space_value[0]}より小さい位置"
                spatial_qualifier_en = f"at a position where the X coordinate is less than {query_pattern_Space_value[0]}"
            elif query_pattern_Space_operator == "y+":
                spatial_qualifier_ja = f"Y座標が{query_pattern_Space_value[1]}より大きい位置"
                spatial_qualifier_en = f"at a position where the Y coordinate is greater than {query_pattern_Space_value[1]}"
            elif query_pattern_Space_operator == "y-":
                spatial_qualifier_ja = f"Y座標が{query_pattern_Space_value[1]}より小さい位置"
                spatial_qualifier_en = f"at a position where the Y coordinate is less than {query_pattern_Space_value[1]}"
            elif query_pattern_Space_operator == "z+":
                spatial_qualifier_ja = f"Z座標が{query_pattern_Space_value[2]}より大きい位置"
                spatial_qualifier_en = f"at a position where the Z coordinate is greater than {query_pattern_Space_value[2]}"
            elif query_pattern_Space_operator == "z-":
                spatial_qualifier_ja = f"Z座標が{query_pattern_Space_value[2]}より小さい位置"
                spatial_qualifier_en = f"at a position where the Z coordinate is less than {query_pattern_Space_value[2]}"
        elif query_pattern_Space_type == "Relation":
            relation = query_pattern_Space_value[0]
            object2_name = query_pattern_Space_value[1]
            if relation == "inside":
                spatial_qualifier_ja = f"{object2_name}の中にある"
                spatial_qualifier_en = f"inside the {object2_name}"
            elif relation == "facing":
                spatial_qualifier_ja = f"{object2_name}から見える位置にある"
                spatial_qualifier_en = f"at a position visible from the {object2_name}"
            elif relation == "on":
                spatial_qualifier_ja = f"{object2_name}の上にある"
                spatial_qualifier_en = f"on the {object2_name}"
            elif relation == "close":
                spatial_qualifier_ja = f"{object2_name}の近くにある"
                spatial_qualifier_en = f"near the {object2_name}"
        else:
            print("query_pattern_Space_type error:", query_pattern_Space_type)
            assert False
        if spatial_qualifier_ja is None:
            spatial_qualifier_ja = ""
        if spatial_qualifier_en is None:
            spatial_qualifier_en = ""
        return spatial_qualifier_ja, spatial_qualifier_en
    
    def getObjectQualifierText(self, query_pattern_Object_type=None, query_pattern_Object_value=None):
        object_qualifier_ja = ""
        object_qualifier_en = ""

        if query_pattern_Object_type == "None":
            if query_pattern_Object_value is None:
                return "", ""
            object_qualifier_ja = f"{query_pattern_Object_value}"
            object_qualifier_en = f"{query_pattern_Object_value}"
        elif query_pattern_Object_type == "Type":
            object_qualifier_ja = f"種類が{query_pattern_Object_value}のもの"
            object_qualifier_en = f"an object whose type is {query_pattern_Object_value}"
        elif query_pattern_Object_type == "Class":
            object_qualifier_ja = f"{query_pattern_Object_value}のサブクラスのもの"
            object_qualifier_en = f"an object which is a subclass of {query_pattern_Object_value}"
        elif query_pattern_Object_type == "State":
            object_qualifier_ja = f"状態が{query_pattern_Object_value}のもの"
            object_qualifier_en = f"an object whose state is {query_pattern_Object_value}"
        elif query_pattern_Object_type == "Attribute":
            object_qualifier_ja = f"属性が{query_pattern_Object_value}のもの"
            object_qualifier_en = f"an object whose attribute is {query_pattern_Object_value}"
        elif query_pattern_Object_type == "Size":
            size = query_pattern_Object_value[0]
            size_operator = query_pattern_Object_value[1]
            axis = query_pattern_Object_value[2]
            size_text_en = ""
            size_text_ja = ""
            if axis == "x":
                size_text_en = "width"
                size_text_ja = "幅"
            elif axis == "y":
                size_text_en = "height"
                size_text_ja = "高さ"
            elif axis == "z":
                size_text_en = "depth"
                size_text_ja = "奥行き"
            else:
                print("Size axis error:", axis)
                assert False
            if size_operator == "<":
                object_qualifier_ja = f"{size_text_ja}が{size}m未満のものに"
                object_qualifier_en = f"an object whose {size_text_en} is less than {size}m"
            elif size_operator == ">":
                object_qualifier_ja = f"{size_text_ja}が{size}mより大きいのものに"
                object_qualifier_en = f"an object whose {size_text_en} is greater than {size}m"
            elif size_operator == "=":
                object_qualifier_ja = f"{size_text_ja}が{size}mのものに"
                object_qualifier_en = f"an object whose {size_text_en} is {size}m"
            elif size_operator == "<=":
                object_qualifier_ja = f"{size_text_ja}が{size}m以下のものに"
                object_qualifier_en = f"an object whose {size_text_en} is less than or equal to {size}m"
            elif size_operator == ">=":
                object_qualifier_ja = f"{size_text_ja}が{size}m以上のものに"
                object_qualifier_en = f"an object whose {size_text_en} is greater than or equal to {size}m"
        else:
            print("query_pattern_Object_type error:", query_pattern_Object_type)
            assert False
        if object_qualifier_ja is None:
            object_qualifier_ja = ""
        if object_qualifier_en is None:
            object_qualifier_en = ""
        
        return object_qualifier_ja, object_qualifier_en
    
    def getActionQualifierText(self, query_pattern_Action_type=None, query_pattern_Action_value=None):
        action_qualifier_ja = ""
        action_qualifier_en = ""
        if query_pattern_Action_type == "None":
            action_qualifier_ja = f"{query_pattern_Action_value}"
            action_qualifier_en = f"{query_pattern_Action_value}"
        else:
            print("query_pattern_Action_type error:", query_pattern_Action_type)
            assert False
        return action_qualifier_ja, action_qualifier_en
    
    def generateText(self, selected_answer_type=None, selected_answer_type_metadata=None, selected_answer_type_metadata_value=None, query_pattern_Action_type=None, query_pattern_Action_value=None, query_pattern_Object_type=None, query_pattern_Object_value=None, query_pattern_Space_type=None, query_pattern_Space_value=None, query_pattern_Space_operator=None, query_pattern_Time_type=None, query_pattern_Time_value=None, query_pattern_Time_operator=None, camera=None):
        text_en = ""
        
        temporal_qualifier_en = ""
        spatial_qualifier_en = ""
        object_qualifier_en = ""
        action_qualifier_en = ""
        # 時間的修飾子
        if selected_answer_type != "Time" and query_pattern_Time_type is not None:
            _, temporal_qualifier_en = self.getTemporalQualifierText(query_pattern_Time_type=query_pattern_Time_type, query_pattern_Time_value=query_pattern_Time_value, query_pattern_Time_operator=query_pattern_Time_operator)
        
        # 空間的修飾子
        if selected_answer_type != "Space" and query_pattern_Space_type is not None:
            _, spatial_qualifier_en = self.getSpatialQualifierText(query_pattern_Space_type=query_pattern_Space_type, query_pattern_Space_value=query_pattern_Space_value, query_pattern_Space_operator=query_pattern_Space_operator)

        # オブジェクト修飾子
        if selected_answer_type != "Object" and query_pattern_Object_type is not None:
            _, object_qualifier_en = self.getObjectQualifierText(query_pattern_Object_type=query_pattern_Object_type, query_pattern_Object_value=query_pattern_Object_value)

        # 動作修飾子
        if selected_answer_type != "Action" and query_pattern_Action_type is not None:
            _, action_qualifier_en = self.getActionQualifierText(query_pattern_Action_type=query_pattern_Action_type, query_pattern_Action_value=query_pattern_Action_value)

        question_json_en = {
            "subject": "agent",
            "time": temporal_qualifier_en,
            "space": spatial_qualifier_en,
            "object": object_qualifier_en,
            "action": action_qualifier_en,
        }
        if selected_answer_type == "Action":
            question_json_en["question"] = "What did the agent do?"
        elif selected_answer_type == "Object":
            if selected_answer_type_metadata == "None":
                question_json_en["question"] = "What is the object?"
            elif selected_answer_type_metadata == "Type":
                question_json_en["question"] = "What is the type of the object?"
            elif selected_answer_type_metadata == "Class":
                question_json_en["question"] = "What is the superclass of the object?"
            elif selected_answer_type_metadata == "State":
                question_json_en["question"] = "What is the state of the object?"
            elif selected_answer_type_metadata == "Attribute":
                question_json_en["question"] = "What is the attribute of the object?"
            elif selected_answer_type_metadata == "Size":
                question_json_en["question"] = "What are the width, height, and depth of the object?"
            else:
                print("selected_answer_type_metadata error:", selected_answer_type_metadata)
                assert False
        elif selected_answer_type == "Time":
            if selected_answer_type_metadata == "Instant":
                question_json_en["question"] = "What is the time?"
            elif selected_answer_type_metadata == "Interval":
                question_json_en["question"] = "From when to when?"
            elif selected_answer_type_metadata == "Duration":
                question_json_en["question"] = "How long?"
            else:
                print("selected_answer_type_metadata error:", selected_answer_type_metadata)
                assert False
        elif selected_answer_type == "Space":
            if selected_answer_type_metadata == "Place":
                question_json_en["question"] = "What is the place?"
            elif selected_answer_type_metadata == "Pos3D":
                question_json_en["question"] = f"What are the 3D spatial coordinates of the object?"
            else:
                print("selected_answer_type_metadata error:", selected_answer_type_metadata)
                assert False
        elif selected_answer_type == "Aggregation":
            if selected_answer_type_metadata == "Count":
                if selected_answer_type_metadata_value == "event":
                    question_json_en["question"] = "How many times?"
                elif selected_answer_type_metadata_value == "object":
                    question_json_en["question"] = "How many times per object?"
                elif selected_answer_type_metadata_value == "place":
                    question_json_en["question"] = "How many times per place?"
            elif selected_answer_type_metadata == "Min":
                if selected_answer_type_metadata_value == "duration":
                    question_json_en["question"] = "What is the shortest duration?"
                elif selected_answer_type_metadata_value == "size_x":
                    question_json_en["question"] = "What is the minimum width of the object?"
                elif selected_answer_type_metadata_value == "size_y":
                    question_json_en["question"] = "What is the minimum height of the object?"
                elif selected_answer_type_metadata_value == "size_z":
                    question_json_en["question"] = "What is the minimum depth of the object?"
                elif selected_answer_type_metadata_value == "pos_x":
                    question_json_en["question"] = f"What is the minimum X coordinate of the {object_qualifier_en}?"
                elif selected_answer_type_metadata_value == "pos_y":
                    question_json_en["question"] = f"What is the minimum Y coordinate of the {object_qualifier_en}?"
                elif selected_answer_type_metadata_value == "pos_z":
                    question_json_en["question"] = f"What is the minimum Z coordinate of the {object_qualifier_en}?"
            elif selected_answer_type_metadata == "Max":
                if selected_answer_type_metadata_value == "duration":
                    question_json_en["question"] = "What is the longest duration?"
                elif selected_answer_type_metadata_value == "size_x":
                    question_json_en["question"] = "What is the maximum width of the object?"
                elif selected_answer_type_metadata_value == "size_y":
                    question_json_en["question"] = "What is the maximum height of the object?"
                elif selected_answer_type_metadata_value == "size_z":
                    question_json_en["question"] = "What is the maximum depth of the object?"
                elif selected_answer_type_metadata_value == "pos_x":
                    question_json_en["question"] = f"What is the maximum X coordinate of the {object_qualifier_en}?"
                elif selected_answer_type_metadata_value == "pos_y":
                    question_json_en["question"] = f"What is the maximum Y coordinate of the {object_qualifier_en}?"
                elif selected_answer_type_metadata_value == "pos_z":
                    question_json_en["question"] = f"What is the maximum Z coordinate of the {object_qualifier_en}?"
            elif selected_answer_type_metadata == "Avg":
                if selected_answer_type_metadata_value == "duration":
                    question_json_en["question"] = "What is the average duration?"
                elif selected_answer_type_metadata_value == "size_x":
                    question_json_en["question"] = "What is the average width of the object?"
                elif selected_answer_type_metadata_value == "size_y":
                    question_json_en["question"] = "What is the average height of the object?"
                elif selected_answer_type_metadata_value == "size_z":
                    question_json_en["question"] = "What is the average depth of the object?"
                elif selected_answer_type_metadata_value == "pos_x":
                    question_json_en["question"] = f"What is the average X coordinate of the {object_qualifier_en}?"
                elif selected_answer_type_metadata_value == "pos_y":
                    question_json_en["question"] = f"What is the average Y coordinate of the {object_qualifier_en}?"
                elif selected_answer_type_metadata_value == "pos_z":
                    question_json_en["question"] = f"What is the average Z coordinate of the {object_qualifier_en}?"
            elif selected_answer_type_metadata == "Sum":
                if selected_answer_type_metadata_value == "duration":
                    question_json_en["question"] = "What is the total duration?"
            else:
                print("selected_answer_type_metadata error:", selected_answer_type_metadata)
                assert False
        elif selected_answer_type == "Activity":
            if selected_answer_type_metadata == "None":
                question_json_en["question"] = "What is the activity?"
            elif selected_answer_type_metadata == "Previous":
                question_json_en["question"] = "What is the previous activity?"
            elif selected_answer_type_metadata == "Next":
                question_json_en["question"] = "What is the next activity?"
            else:
                print("selected_answer_type_metadata error:", selected_answer_type_metadata)
                assert False
        elif selected_answer_type == "Video":
            if selected_answer_type_metadata == "Video":
                question_json_en["question"] = f"What is the video from {camera}?"
            elif selected_answer_type_metadata == "VideoFrame":
                question_json_en["question"] = f"What are the start and end frames of the scene from {camera}?"
            elif selected_answer_type_metadata == "Pos2D":
                if selected_answer_type_metadata_value == "max":
                    question_json_en["question"] = f"What are the objects and their bounding boxes in the last video frame from {camera}?"
                else:
                    question_json_en["question"] = f"What are the objects and their bounding boxes in the first video frame from {camera}?"

            else:
                print("selected_answer_type_metadata error:", selected_answer_type_metadata)
                assert False

        
        # llmを使ってjsonから質問文を生成
        text_en = self.convertJsonToQuestionTextEN(question_json_en)

        return text_en, question_json_en
    
    def convertJsonToQuestionTextEN(self, question_json_en):
        # llmを使ってjsonから質問文を生成
        messages = [
            {"role": "system", "content": "You are an assistant who helps create question texts based on JSON provided by users. Based on the following JSON, create a question text for question answering over knowledge graph. Use the values in JSON as they are, without changing the words.　Do not output anything other than the question text."}
        ]
        prompt1 = f"""
            JSON:
            {{
                "subject": "agent",
                "time": "after 2024-04-02T16:28:00 and before or at 2024-07-03T14:39:00",
                "space": "at a position where the Y coordinate is less than 2.4",
                "object": "an object whose attribute is has_plug",
                "action": "type",
                "question": "What is the next activity?"
            }}

            Question text:
        """
        prompt1 = textwrap.dedent(prompt1).strip()
        messages.append(
            {"role": "user", "content": prompt1}
        )
        messages.append(
            {"role": "assistant", "content": "What is the next activity involving an agent that types an object whose attribute is has_plug at a position where the Y coordinate is less than 2.4 after 2024-04-02T16:28:00 and before or at 2024-07-03T14:39:00?"}
        )
        prompt2 = f"""
            JSON:
            {{
                "subject": "agent",
                "time": "more than or equal to 14 seconds",
                "space": "at a position where the X coordinate is less than 2.03",
                "object": "an object whose type is Waterglass",
                "action": "shake",
                "question": "What is the video?"
            }}

            Question text:
        """
        prompt2 = textwrap.dedent(prompt2).strip()
        messages.append(
            {"role": "user", "content": prompt2}
        )
        messages.append(
            {"role": "assistant", "content": "What is the video involving an agent that shakes an object whose type is Waterglass at a position where the X coordinate is less than 2.03 for more than or equal to 14 seconds?"}
        )
        prompt3 = f"""
            JSON:
            {{
                "subject": "agent",
                "time": "after 2024-05-12T22:37:00 and before or at 2024-06-23T00:20:00",
                "space": "bathroom",
                "object": "",
                "action": "soak",
                "question": "What are the width, height, and depth of the object?"
            }}

            Question text:
        """
        prompt3 = textwrap.dedent(prompt3).strip()
        messages.append(
            {"role": "user", "content": prompt3}
        )
        messages.append(
            {"role": "assistant", "content": "What are the width, height, and depth of the object soaked by an agent in the bathroom after 2024-05-12T22:37:00 and before or at 2024-06-23T00:20:00?"}
        )
        # 最後のユーザープロンプト
        prompt4 = f"""
            JSON:
            {json.dumps(question_json_en, indent=4)}

            Question text:
        """
        prompt4 = textwrap.dedent(prompt4).strip()
        messages.append(
            {"role": "user", "content": prompt4}
        )

        client = OpenAI(api_key = os.environ["OPENAI_API_KEY"])
        generated_question_text_en = ""

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            generated_question_text_en = completion.choices[0].message.content
            # 後処理
            for tag in ("```Question text:", "```", "question:", "Question:", "### Question text:", "Answer:"):
                generated_question_text_en = generated_question_text_en.replace(tag, "")
            print(generated_question_text_en)
        except Exception as e:
            print(f"Error generating question text: {e}")
            generated_question_text_en = "Error generating question text." 

        return generated_question_text_en
    

    def generateSPARQL(self, 
                       selected_answer_type=None, 
                       selected_answer_type_metadata=None, 
                       selected_answer_type_metadata_value=None, 
                       object_query_pattern=None, 
                       action_query_pattern=None, 
                       spatial_query_pattern=None, 
                       temporal_query_pattern=None, 
                       query_pattern_Action_value=None, 
                       query_pattern_Object_type=None, 
                       query_pattern_Time_type=None, 
                       query_pattern_Space_type=None,
                       camera=None):
        query = None 

        sparql_header = "SELECT DISTINCT ?answer"
        query_footer = "limit 1"

        # 時間のソート順を決定
        temporal_query_footer = ""
        if query_pattern_Time_type == "First":
            temporal_query_footer = "order by asc(?begin_time)"
        elif query_pattern_Time_type == "Last" or query_pattern_Time_type == "Current":
            temporal_query_footer = "order by desc(?end_time)"

        # 問う対象によりクエリテンプレートを変更
        if selected_answer_type == "Action": #Aを問う場合
            if selected_answer_type_metadata == "None":
                query_pattern_Action_triple = f"""
                    ?event vh2kg:action ?answer .
                """
            else:
                # pending
                assert False
            if query_pattern_Time_type == "Interval": #TのパターンがIntervalの場合、タイムアウトを考慮してクエリを分割
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {object_query_pattern}
                        {spatial_query_pattern}
                        }} }}
                        {temporal_query_pattern}
                        {query_pattern_Action_triple}
                    }} {query_footer}
                """
            else:
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {object_query_pattern}
                        {temporal_query_pattern}
                        }} {temporal_query_footer} }}
                        {spatial_query_pattern}
                        {query_pattern_Action_triple}
                    }} {query_footer}
                """
            
        elif selected_answer_type == "Object": #Oを問う場合
            if selected_answer_type_metadata == "None":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?answer .
                """
            elif selected_answer_type_metadata == "Type":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?object rdf:type ?answer .
                """
            elif selected_answer_type_metadata == "Class":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?object rdf:type ?objectType .
                    ?objectType rdfs:subClassOf ?answer .
                """
            elif selected_answer_type_metadata == "State":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?state vh2kg:isStateOf ?object .
                    ?state vh2kg:state ?answer .
                """
            elif selected_answer_type_metadata == "Attribute":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?object vh2kg:attribute ?answer .
                """
            elif selected_answer_type_metadata == "Size":
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?state vh2kg:isStateOf ?object .
                    ?state vh2kg:bbox ?shape .
                    ?shape x3do:bboxSize ?size .
                    ?size rdf:first ?size_x ;
                        rdf:rest/rdf:first ?size_y ;
                        rdf:rest/rdf:rest/rdf:first ?size_z .
                """
                sparql_header = "SELECT DISTINCT ?size_x ?size_y ?size_z"
            else:
                assert False

            query_pattern_Object_triple_list = query_pattern_Object_triple.split("\n")
            for triple in query_pattern_Object_triple_list:
                if "?event vh2kg:mainObject ?object" in spatial_query_pattern:
                    if "?event vh2kg:mainObject ?object ." in triple:
                        query_pattern_Object_triple_list.remove(triple)
                elif "?state vh2kg:isStateOf ?object" in spatial_query_pattern:
                    if "?state vh2kg:isStateOf ?object ." in triple:
                        query_pattern_Object_triple_list.remove(triple)
                else:
                    break
            
            query = f"""
                {self.prefix}
                {sparql_header} WHERE {{
                    {{ select * where {{
                    {action_query_pattern}
                    {temporal_query_pattern}
                    }} {temporal_query_footer} }}
                    {spatial_query_pattern}
                    {query_pattern_Object_triple}
                }} {query_footer}
            """

        elif selected_answer_type == "Time": #Tを問う場合
            if selected_answer_type_metadata == "Instant":
                query_pattern_Time_triple = """
                    ?event vh2kg:time ?time_interval .
                    ?time_interval time:hasBeginning ?begin .
                    ?begin time:inXSDDateTime ?answer .
                """
                text_header = "When did the event happen?"
            elif selected_answer_type_metadata == "Interval":
                query_pattern_Time_triple = """
                    ?event vh2kg:time ?time_interval .
                    ?time_interval time:hasBeginning ?begin .
                    ?begin time:inXSDDateTime ?begin_time .
                    ?time_interval time:hasEnd ?end .
                    ?end time:inXSDDateTime ?end_time .
                """
                sparql_header = "SELECT DISTINCT ?begin_time ?end_time"
                text_header = "When did the event start and finish"
            elif selected_answer_type_metadata == "Duration":
                query_pattern_Time_triple = """
                    ?event vh2kg:time ?time .
                    ?time time:numericDuration ?answer .
                """
                text_header = "How long did the event take?"
            else:
                # current, first, last, previous, nextの値(event)を問うことはない
                assert False
            
            query = f"""
                {self.prefix}
                {sparql_header} WHERE {{
                    {{ select * where {{
                    {action_query_pattern}
                    {object_query_pattern}
                    }} }}
                    {spatial_query_pattern}
                    {query_pattern_Time_triple}
                }} {query_footer}
            """
        elif selected_answer_type == "Space":
            if selected_answer_type_metadata == "Place":
                is_from_to = False
                if query_pattern_Action_value == "walk":
                    is_from_to = True

                if is_from_to:
                    query_pattern_Space_triple = "?event vh2kg:from ?from ; vh2kg:to ?to ."
                    sparql_header = "SELECT DISTINCT ?from ?to"
                    text_header = "Where did the event happen from and to?"
                else:
                    query_pattern_Space_triple = "?event vh2kg:place ?answer ."
                    text_header = "Where did the event happen?"
            elif selected_answer_type_metadata == "Pos3D":
                if query_pattern_Object_type == "size":
                    query_pattern_Space_triple = """
                        ?shape x3do:bboxCenter ?pos .
                        ?pos rdf:first ?pos_x ;
                            rdf:rest/rdf:first ?pos_y ;
                            rdf:rest/rdf:rest/rdf:first ?pos_z .
                    """
                elif query_pattern_Object_type == "state":
                    query_pattern_Space_triple = """
                        ?state vh2kg:partOf ?situation .
                        ?state vh2kg:isStateOf ?object .
                        ?state vh2kg:bbox ?bbox .
                        ?bbox x3do:bboxCenter ?pos .
                        ?pos rdf:first ?pos_x ;
                            rdf:rest/rdf:first ?pos_y ;
                            rdf:rest/rdf:rest/rdf:first ?pos_z .
                    """
                else:
                    query_pattern_Space_triple = """
                        ?event vh2kg:mainObject ?object .
                        ?event vh2kg:situationAfterEvent ?situation .
                        ?state vh2kg:partOf ?situation .
                        ?state vh2kg:isStateOf ?object .
                        ?state vh2kg:bbox ?bbox .
                        ?bbox x3do:bboxCenter ?pos .
                        ?pos rdf:first ?pos_x ;
                            rdf:rest/rdf:first ?pos_y ;
                            rdf:rest/rdf:rest/rdf:first ?pos_z .
                    """
                sparql_header = "SELECT DISTINCT ?pos_x ?pos_y ?pos_z"
                text_header = "Where are the object's coordinates?"
            # elif selected_answer_type_metadata == "Relation": # 実行が終了しないためpending
            #     # is_property = random.choice([True, False])
            #     object2_name = query_pattern_Space_value[1]
            #     # if is_property:
            #     query_pattern_Space_triple = f"""
            #         ?event vh2kg:situationAfterEvent ?situation .
            #         ?state vh2kg:partOf ?situation .
            #         ?state vh2kg:isStateOf ?object .
            #         ?state vh2kg:bbox ?shape .
            #         ?shape ?answer ?shape2 .
            #         ?state2 vh2kg:bbox ?shape2 ;
            #             vh2kg:isStateOf ?object2 .
            #         {{
            #             select * where {{
            #                 ?object2 rdfs:label "{object2_name}" .
            #             }}
            #         }}
            #     """
            #         # text_header = f"What is the relation between the {object_name1} and {object2_name}?"
            #     # else:
            #     #     relation = random.choice(spatial_relations)
            #     #     query_pattern_Space_triple = """
            #     #         ?event vh2kg:mainObject ?object .
            #     #         ?event vh2kg:situationAfterEvent ?situation .
            #     #         ?state vh2kg:partOf ?situation .
            #     #         ?state vh2kg:isStateOf ?object .
            #     #         ?object rdfs:label "{}" .
            #     #         ?state vh2kg:bbox ?bbox .
            #     #         ?bbox <{}> ?bbox2 .
            #     #         ?state2 vh2kg:bbox ?bbox2 .
            #     #         ?state2 vh2kg:isStateOf ?answer .
            #     #     """.format(object_name1, relation)
            #     #     text_header = f"What is the object {relation.replace(vh2kg, "")} of {object_name1}?"
            # elif selected_answer_type_metadata == "Pos2D":
            #     query_pattern_Space_triple = """
            #         ?vs vh2kg:isVideoSegmentOf ?event ;
            #             mssn:hasMediaDescriptor ?frame .
            #         ?frame mssn:hasMediaDescriptor ?bbox2d .
            #         ?bbox2d vh2kg:is2DbboxOf ?object ;
            #                 vh2kg:bbox-2d-value ?answer .
            #     """
            #     text_header = "Where is the object in the frame?"
            else:
                print("Space")
                assert False
            
            query = f"""
                {self.prefix}
                {sparql_header} WHERE {{
                    {{ select * where {{
                    {action_query_pattern}
                    {object_query_pattern}
                    {temporal_query_pattern}
                    }} {temporal_query_footer} }}
                    {query_pattern_Space_triple}
                }} {query_footer}
            """
        elif selected_answer_type == "Aggregation":
            if selected_answer_type_metadata == "Count":
                sparql_header = f"SELECT (COUNT(DISTINCT ?{selected_answer_type_metadata_value}) as ?answer)"
            elif selected_answer_type_metadata == "Min" or selected_answer_type_metadata == "Max" or selected_answer_type_metadata == "Avg":
                sparql_header = f"SELECT DISTINCT ({selected_answer_type_metadata.upper()}(?{selected_answer_type_metadata_value}) as ?answer)"
            elif selected_answer_type_metadata == "Sum":
                sparql_header = f"SELECT DISTINCT (SUM(?duration) as ?answer)"
            else:
                print("selected_answer_type_metadata", selected_answer_type_metadata)
                assert False
            
            if selected_answer_type_metadata_value == "event":
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {action_query_pattern}
                        {object_query_pattern}
                        }} }}
                        {temporal_query_pattern}
                        {spatial_query_pattern}
                    }}
                """
            elif selected_answer_type_metadata_value == "object":
                sparql_header = f"SELECT DISTINCT ?object (COUNT(distinct ?event) as ?answer)"
                # query_pattern_Object_triple = """
                #     ?event vh2kg:mainObject ?object . 
                # """
                # if "?event vh2kg:mainObject ?object" in spatial_query_pattern:
                #     query_pattern_Object_triple = ""
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {action_query_pattern}
                        {object_query_pattern}
                        }} }}
                        {spatial_query_pattern}
                        {temporal_query_pattern}
                    }} group by ?object
                """
            elif selected_answer_type_metadata_value == "place":
                sparql_header = f"SELECT DISTINCT ?place (COUNT(?event as ?answer)"
                query_pattern_Space_triple = ""
                if "?event vh2kg:place ?place" not in spatial_query_pattern:
                    query_pattern_Space_triple = "?event vh2kg:place ?place ."
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select distinct ?event where {{
                        {action_query_pattern}
                        {object_query_pattern}
                        }} }}
                        {temporal_query_pattern}
                        {query_pattern_Space_triple}
                    }} group by ?place
                """
            elif selected_answer_type_metadata_value == "duration":
                query_pattern_Time_triple = ""
                if "?time_duration time:numericDuration ?duration" not in temporal_query_pattern:    
                    query_pattern_Time_triple = (
                        "?time_duration time:numericDuration ?duration ."
                        if "?event vh2kg:time ?time_duration" in temporal_query_pattern
                        else "?event vh2kg:time ?time_duration .\n?time_duration time:numericDuration ?duration ."
                    )
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select distinct ?event where {{
                        {action_query_pattern}
                        {object_query_pattern}
                        {spatial_query_pattern}
                        }} }}
                        {temporal_query_pattern}
                        {query_pattern_Time_triple}
                    }}
                """
            elif selected_answer_type_metadata_value in ["size_x", "size_y", "size_z"]:
                query_pattern_Object_triple = f"""
                    ?event vh2kg:mainObject ?object .
                    ?state vh2kg:isStateOf ?object .
                    ?state vh2kg:bbox ?shape .
                    ?shape x3do:bboxSize ?size .
                    ?size rdf:first ?size_x ;
                        rdf:rest/rdf:first ?size_y ;
                        rdf:rest/rdf:rest/rdf:first ?size_z .
                """
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {action_query_pattern}
                        {object_query_pattern}
                        {temporal_query_pattern}
                        }} }}
                        {spatial_query_pattern}
                        {query_pattern_Object_triple}
                    }}
                """
            elif selected_answer_type_metadata_value in ["pos_x", "pos_y", "pos_z"]:
                if query_pattern_Object_type == "size":
                    query_pattern_Space_triple = """
                        ?shape x3do:bboxCenter ?pos .
                        ?pos rdf:first ?pos_x ;
                            rdf:rest/rdf:first ?pos_y ;
                            rdf:rest/rdf:rest/rdf:first ?pos_z .
                    """
                elif query_pattern_Object_type == "state":
                    query_pattern_Space_triple = """
                        ?state vh2kg:partOf ?situation .
                        ?state vh2kg:isStateOf ?object .
                        ?state vh2kg:bbox ?bbox .
                        ?bbox x3do:bboxCenter ?pos .
                        ?pos rdf:first ?pos_x ;
                            rdf:rest/rdf:first ?pos_y ;
                            rdf:rest/rdf:rest/rdf:first ?pos_z .
                    """
                else:
                    query_pattern_Space_triple = """
                        ?event vh2kg:mainObject ?object .
                        ?event vh2kg:situationAfterEvent ?situation .
                        ?state vh2kg:partOf ?situation .
                        ?state vh2kg:isStateOf ?object .
                        ?state vh2kg:bbox ?bbox .
                        ?bbox x3do:bboxCenter ?pos .
                        ?pos rdf:first ?pos_x ;
                            rdf:rest/rdf:first ?pos_y ;
                            rdf:rest/rdf:rest/rdf:first ?pos_z .
                    """
                    if "?event vh2kg:mainObject ?object" not in object_query_pattern:
                        query_pattern_Space_triple = "?event vh2kg:mainObject ?object .\n" + query_pattern_Space_triple
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {action_query_pattern}
                        {temporal_query_pattern}
                        }} }}
                        {spatial_query_pattern}
                        {object_query_pattern}
                        {query_pattern_Space_triple}
                    }}
                """
            else:
                print("selected_answer_type_metadata_value", selected_answer_type_metadata_value)
                print("selected_answer_type_metadata", selected_answer_type_metadata)
                print("selected_answer_type", selected_answer_type)
                # デフォルトのSpace処理（すべてのタイプで共通）
                query_pattern_Space_triple = """
                    ?event vh2kg:mainObject ?object .
                    ?event vh2kg:situationAfterEvent ?situation .
                    ?state vh2kg:partOf ?situation .
                    ?state vh2kg:isStateOf ?object .
                    ?state vh2kg:bbox ?bbox .
                    ?bbox x3do:bboxCenter ?pos .
                    ?pos rdf:first ?pos_x ;
                        rdf:rest/rdf:first ?pos_y ;
                        rdf:rest/rdf:rest/rdf:first ?pos_z .
                """
                if "?event vh2kg:mainObject ?object" not in object_query_pattern:
                    query_pattern_Space_triple = "?event vh2kg:mainObject ?object .\n" + query_pattern_Space_triple
                query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {action_query_pattern}
                        {temporal_query_pattern}
                        }} }}
                        {spatial_query_pattern}
                        {object_query_pattern}
                        {query_pattern_Space_triple}
                    }}
                """
        
        elif selected_answer_type == "Activity":
            query_pattern_Activity_triple = ""
            if selected_answer_type_metadata == "None":
                query_pattern_Activity_triple = "?answer vh2kg:hasEvent ?event ."
            elif selected_answer_type_metadata == "Previous":
                query_pattern_Activity_triple = """
                    ?activity vh2kg:hasEvent ?event .
                    ?answer vh2kg:nextActivity ?activity .
                """
            elif selected_answer_type_metadata == "Next":
                query_pattern_Activity_triple = """
                    ?activity vh2kg:hasEvent ?event .
                    ?activity vh2kg:nextActivity ?answer .
                """
            else:
                print("selected_answer_type_metadata", selected_answer_type_metadata)
                assert False

            query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {action_query_pattern}
                        {temporal_query_pattern}
                        }} }}
                        {object_query_pattern}
                        {spatial_query_pattern}
                        {query_pattern_Activity_triple}
                    }} {query_footer}
                """
        elif selected_answer_type == "Video":
            query_pattern_Video_triple = ""
            if selected_answer_type_metadata == "Video":
                query_pattern_Video_triple = f"""
                ?vs vh2kg:isVideoSegmentOf ?event .
                ?md mssn:hasMediaSegment ?vs ;
                    sosa:madeBySensor ex:{camera}_{self.scene} ;
                    vh2kg:video ?answer .
                """
            elif selected_answer_type_metadata == "VideoFrame":
                sparql_header = f"SELECT DISTINCT ?minFrame ?maxFrame"
                query = f"""
                {self.prefix}
                {sparql_header} WHERE {{
                    {{
                        SELECT ?vs (MIN(?num) AS ?minNum) (MAX(?num) AS ?maxNum)
                        WHERE {{
                            {{ SELECT * WHERE {{
                                {action_query_pattern}
                                {temporal_query_pattern}
                                {object_query_pattern}
                                {spatial_query_pattern}
                            }} }}
                            ?vs vh2kg:isVideoSegmentOf ?event ;
                                mssn:hasMediaDescriptor ?frame .
                            ?md mssn:hasMediaSegment ?vs ; sosa:madeBySensor ex:{camera}_{self.scene} .
                            ?frame vh2kg:frameNumber ?num .
                        }} GROUP BY ?vs limit 1
                    }}
                    ?vs mssn:hasMediaDescriptor ?minFrame .
                    ?minFrame vh2kg:frameNumber ?minNum .

                    ?vs mssn:hasMediaDescriptor ?maxFrame .
                    ?maxFrame vh2kg:frameNumber ?maxNum .
                }} {query_footer}
                """
                return query
            elif selected_answer_type_metadata == "Pos2D":
                sparql_header = f"SELECT DISTINCT ?visible_object ?pos2d"
                operation = selected_answer_type_metadata_value
                query = f"""
                {self.prefix}
                {sparql_header} WHERE {{
                    {{
                        SELECT ?vs ({operation.capitalize()}(?num) AS ?{operation}Num)
                        WHERE {{
                            {{ SELECT * WHERE {{
                            {action_query_pattern}
                            {temporal_query_pattern}
                            {object_query_pattern}
                            {spatial_query_pattern}
                            }} }}
                            ?vs vh2kg:isVideoSegmentOf ?event ;
                                mssn:hasMediaDescriptor ?frame .
                            ?md mssn:hasMediaSegment ?vs ; sosa:madeBySensor ex:{camera}_{self.scene} .
                            ?frame vh2kg:frameNumber ?num .
                        }} GROUP BY ?vs limit 1
                    }}
                    ?vs mssn:hasMediaDescriptor ?{operation}Frame .
                    ?{operation}Frame vh2kg:frameNumber ?{operation}Num ;
                                mssn:hasMediaDescriptor ?bbox .
                    ?bbox a mssn:BoundingBoxDescriptor ;
                            vh2kg:bbox-2d-value ?pos2d ;
                        vh2kg:is2DbboxOf ?visible_object .
                }}
                """
                return query

            
            query = f"""
                    {self.prefix}
                    {sparql_header} WHERE {{
                        {{ select * where {{
                        {action_query_pattern}
                        {temporal_query_pattern}
                        }} }}
                        {object_query_pattern}
                        {spatial_query_pattern}
                        {query_pattern_Video_triple}
                    }} {query_footer}
                """

        else:
            print("selected_answer_type", selected_answer_type)
            assert False

        return query
    
    def execSPARQL(self, query):
        results = None
        sparql = SPARQLWrapper(self.repository)
        sparql.addParameter('infer', 'false')
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        try :
            json = sparql.query().convert()
            results = json["results"]["bindings"]
        except  Exception as e:
            print(e.args)
        return results
