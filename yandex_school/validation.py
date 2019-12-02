from datetime import datetime
from typing import List, Tuple, Dict

from marshmallow import Schema, fields, pre_load, ValidationError
from marshmallow.validate import Range, Length


class DateField(fields.Date):
    """
    Custom Date field for Marshmallow. Allows processing raw data before it gets converted.
    The only purpose is to check whether given date format corresponds to <dd.mm.YYYY> including
    trailing zeros.
    """

    def _deserialize(self, value, attr, obj, **kwargs):
        if len(value) != 10:
            raise ValidationError('Wrong date format!')
        return super(DateField, self)._deserialize(value, attr, obj, **kwargs)


class CitizenSchema(Schema):
    class Meta:
        ordered = True

    citizen_id = fields.Integer(required=True, strict=True, validate=[Range(min=1)])
    town = fields.Str(required=True, validate=[Length(min=1, max=256)])
    street = fields.Str(required=True, validate=[Length(min=1, max=256)])
    building = fields.Str(required=True, validate=[Length(min=1, max=256)])
    apartment = fields.Integer(required=True, strict=True, validate=[Range(min=1)])
    name = fields.Str(required=True, validate=[Length(min=1, max=256)])
    birth_date = DateField(required=True, format='%d.%m.%Y', validate=[lambda x: x < datetime.date(datetime.utcnow())])
    gender = fields.Str(required=True, validate=[lambda x: x == 'male' or x == 'female'])
    relatives = fields.List(fields.Integer(strict=True, validate=[Range(min=1)]), required=True)

    @pre_load(pass_many=True)
    def remove_envelope(self, data, many, **kwargs):
        if many:
            return data['citizens']
        else:
            return data


citizenSchema = CitizenSchema()
citizensSchema = CitizenSchema(many=True)


def validate_relatives(citizens: List[Dict]) -> List[Tuple[int, int]]:
    """
    Makes sure all relationships are mutual and all relative_ids are present in the dataset.
    :param citizens: list of citizens where each citizen is a dict
    :return: relationship links list. e.g.: if citizens 1 and 2 are related, you'll get [(1, 2), (2, 1)]
    """
    relative_links = []
    # for faster lookups
    lookup_dict = {x['citizen_id']: x['relatives'] for x in citizens}
    for citizen, relatives in lookup_dict.items():
        for relative in relatives:
            relative_links.append((citizen, relative))
            try:
                if citizen not in lookup_dict[relative]:
                    raise ValidationError(f'Relationship between {citizen} and {relative} is not mutual!')
            except KeyError:
                raise ValidationError(f'Citizen {citizen} has got an unexistent relative {relative}')
    return relative_links


def validate_citizen_ids(citizens: List[Dict]) -> None:
    """
    Check if all the citizen_ids are unique. This function adds them all into a set and checks
    if set's length equals to citizens list length.
    :param citizens: list of citizens where each citizen is a dict
    :return: None
    """
    ids = {citizen['citizen_id'] for citizen in citizens}
    if len(citizens) != len(ids):
        raise ValidationError('Duplicate citizen_id found!')
