from core.model import ModelWrapper

from maxfw.core import MAX_API, PredictAPI, MetadataAPI
from flask_restplus import fields
from flask import request
from werkzeug.datastructures import FileStorage


model_wrapper = ModelWrapper()

# === Labels API

model_label = MAX_API.model('ModelLabel', {
    'id': fields.String(required=True, description='Label identifier'),
    'name': fields.String(required=True, description='Entity label'),
    'description': fields.String(required=False, description='Meaning of entity label')
})

labels_response = MAX_API.model('LabelsResponse', {
    'count': fields.Integer(required=True, description='Number of labels returned'),
    'labels': fields.List(fields.Nested(model_label), description='Entity labels that can be predicted by the model')
})

# Reference: http://gmb.let.rug.nl/manual.php
tag_desc = {
    'B-PER': 'Person; entities are limited to individuals that are human or have human characteristics, such as divine entities. B- tag indicates start of a new phrase.',
    'I-PER': 'Person; entities are limited to individuals that are human or have human characteristics, such as divine entities.',
    'B-GEO': 'Location; entities are limited to geographical entities such as geographical areas and landmasses, bodies of water, and geological formations. B- tag indicates start of a new phrase.',
    'I-GEO': 'Location; entities are limited to geographical entities such as geographical areas and landmasses, bodies of water, and geological formations.',
    'B-ORG': 'Organization; entities are limited to corporations, agencies, and other groups of people defined by an established organizational structure. B- tag indicates start of a new phrase.',
    'I-ORG': 'Organization; entities are limited to corporations, agencies, and other groups of people defined by an established organizational structure',
    'B-GPE': 'Geo-political Entity; entities are geographical regions defined by political and/or social groups. A GPE entity subsumes and does not distinguish between a city, a nation, its region, its government, or its people. B- tag indicates start of a new phrase.',
    'I-GPE': 'Geo-political Entity; entities are geographical regions defined by political and/or social groups. A GPE entity subsumes and does not distinguish between a city, a nation, its region, its government, or its people',
    'B-TIM': 'Time; limited to references to certain temporal entities that have a name, such as the days of the week and months of a year. B- tag indicates start of a new phrase.',
    'I-TIM': 'Time; limited to references to certain temporal entities that have a name, such as the days of the week and months of a year.',
    'B-EVE': 'Event; incidents and occasions that occur during a particular time. B- tag indicates start of a new phrase.',
    'I-EVE': 'Event; incidents and occasions that occur during a particular time.',
    'B-ART': 'Artifact; limited to manmade objects, structures and abstract entities, including buildings, facilities, art and scientific theories. B- tag indicates start of a new phrase.',
    'I-ART': 'Artifact; limited to manmade objects, structures and abstract entities, including buildings, facilities, art and scientific theories.',
    'B-NAT': 'Natural Object; entities that occur naturally and are not manmade, such as diseases, biological entities and other living things. B- tag indicates start of a new phrase.',
    'I-NAT': 'Natural Object; entities that occur naturally and are not manmade, such as diseases, biological entities and other living things.',
    'O': 'No entity type'
}

class ModelLabelsAPI(MetadataAPI):
    '''API for getting information about available entity tags'''
    @MAX_API.doc('get_labels')
    @MAX_API.marshal_with(labels_response)
    def get(self):
        '''Return the list of labels that can be predicted by the model'''
        result = {}
        result['labels'] = [{'id': l[0], 'name': l[1], 'description': tag_desc[l[1]]} for l in model_wrapper.id_to_tag.items()]
        result['count'] = len(model_wrapper.id_to_tag)
        return result

# === Predict API 

input_example = 'John lives in Brussels and works for the EU'
ent_example = ['I-PER', 'O', 'O', 'I-LOC', 'O', 'O', 'O', 'O', 'I-ORG']
term_example = ['John', 'lives', 'in', 'Brussels', 'and', 'works', 'for', 'the', 'EU']

model_input = MAX_API.model('ModelInput', {
    'text': fields.String(required=True, description='Text for which to predict entities', example=input_example)
})

model_prediction = MAX_API.model('ModelPrediction', {
    'tags': fields.List(fields.String, required=True, description='List of predicted entity tags, one per term in the input text.', example=ent_example),
    'terms': fields.List(fields.String, required=True, 
        description='Terms extracted from input text pre-processing. Each term has a corresponding predicted entity tag in the "tags" field.',
        example=term_example)
})

predict_response = MAX_API.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'prediction': fields.Nested(model_prediction, description='Model prediction')
})

class ModelPredictAPI(PredictAPI):

    @MAX_API.doc('predict')
    @MAX_API.expect(model_input)
    @MAX_API.marshal_with(predict_response)
    def post(self):
        '''Make a prediction given input data'''
        result = {'status': 'error'}

        j = request.get_json()
        text = j['text']
        entities, terms = model_wrapper.predict(text)
        model_pred = {
            'tags': entities,
            'terms': terms
        }
        result['prediction'] = model_pred
        result['status'] = 'ok'

        return result
