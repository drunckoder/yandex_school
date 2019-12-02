from typing import List, Dict, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta

from flask import request
from flask_restful import Resource
from marshmallow import ValidationError
import numpy

from yandex_school import db
from yandex_school.models import Import, Citizen, Relative
from yandex_school.validation import citizenSchema, citizensSchema, validate_relatives, validate_citizen_ids


class CreateImport(Resource):
    """
        Serves /imports endpoint
    """

    @staticmethod
    def store_relationships(import_id: int, relative_links: List[Tuple]) -> None:
        """
        Maps citizen_ids to database ids, pushes relationships into database
        :param import_id: id of current import
        :param relative_links: relationship links list of citizen_ids
        :return: None
        """
        # get citizens ids of the current import
        id_list = db.engine.execute(
            db.select([Citizen.c.id, Citizen.c.citizen_id]).where(Citizen.c.import_id == import_id)
        ).fetchall()
        # map database ids to citizen ids
        rev_id_map = {k: v for v, k in id_list}
        # create relationships
        relationships = [{'citizen_id': rev_id_map[citizen], 'relative_id': rev_id_map[relative]}
                         for citizen, relative in relative_links]
        # push into database
        db.engine.execute(Relative.insert(), relationships)

    def post(self):
        """
        Post request handler
        """
        try:
            # validates data, returns objects
            citizens = citizensSchema.load(request.json)
            # check if there are no citizens
            if not citizens:
                raise ValidationError('No citizens were present in the request body')
            # check if ids are correct
            validate_citizen_ids(citizens)
            # validates relatives, returns relationship tuples
            relative_links = validate_relatives(citizens)
        except ValidationError as ex:
            return {'message': f'Validation error', 'errors': ex.messages}, 400
        except KeyError as ex:
            return {'message': f'Expected key {ex} not found in the request body'}, 400
        except TypeError as ex:
            return {'message': f'Malformed data', 'errors': ex}, 400

        # putting new import record into db and getting resulting primary key back
        import_id = db.engine.execute(Import.insert(), [{}]).inserted_primary_key[0]

        # assigning IDs manually as bulk saving ignores
        # relationships
        for citizen in citizens:
            citizen['import_id'] = import_id

        # putting citizens into db
        db.engine.execute(Citizen.insert(), citizens)

        # store relationships only if they exist
        if relative_links:
            self.store_relationships(import_id, relative_links)

        return {'data': {'import_id': import_id}}, 201


class PatchCitizen(Resource):
    """
        Serves /imports/<int:import_id>/citizens/<int:citizen_id> endpoint
    """

    @staticmethod
    def get_relatives_diff(import_id: int, citizen_id: int, requested_relatives: list) -> Tuple[int, list, list]:
        """
        Calculates relative changes to be made by request.
        :param import_id: requested import_id
        :param citizen_id: requested citizen_id
        :param requested_relatives: proposed relatives, should be final state of the operation
        :return: citizen's database id, list of new relatives, list of lost relatives. All ids are database ids.
        """

        def get_diff(cur: List[int], req: List[int]) -> Tuple[set, set]:
            """
            Sub-function for set difference operations
            :param cur: current relatives
            :param req: proposed relatives
            :return: list of citizen_ids to be added and to be removed from relatives
            """
            cur, req, add, rem = set(cur), set(req), set(), set()
            rem = cur - req
            add = cur - rem ^ req
            return add, rem

        join = Citizen.outerjoin(Relative, Relative.c.citizen_id == Citizen.c.id)
        raw_relatives = db.engine.execute(
            db.select([Relative.c.relative_id])
                .where(Citizen.c.import_id == import_id)
                .where(Citizen.c.citizen_id == citizen_id)
                .select_from(join)
        ).fetchall()

        id_list = db.engine.execute(
            db.select([Citizen.c.id, Citizen.c.citizen_id]).where(Citizen.c.import_id == import_id)
        )

        id_map = {k: v for k, v in id_list}
        rev_id_map = {k: v for v, k in id_map.items()}

        # raises KeyError if citizen_id does not exist
        db_citizen_id = rev_id_map[citizen_id]

        if not all([citizen_id in rev_id_map for citizen_id in requested_relatives]):
            raise ValidationError(f'Citizen relatives contain unexistent citizen_id')

        current_relatives = list(map(id_map.get, *zip(*raw_relatives)))

        add_list, rem_list = get_diff(current_relatives, requested_relatives)

        add_list = list(map(rev_id_map.get, add_list))
        rem_list = list(map(rev_id_map.get, rem_list))

        add_links = []

        for x in add_list:
            add_links.append({'citizen_id': db_citizen_id, 'relative_id': x})
            add_links.append({'citizen_id': x, 'relative_id': db_citizen_id})

        return db_citizen_id, add_links, rem_list

    def process_relatives(self, import_id: int, citizen_id: int, requested_relatives: list) -> int:
        """
        Pushes relationship changes into database
        :param import_id: requested import_id
        :param citizen_id: requested citizen_id
        :param requested_relatives: proposed relatives, should be final state of the operation
        :return: citizen's database id.
        """
        db_citizen_id, add_links, rem_list = self.get_relatives_diff(import_id, citizen_id, requested_relatives)

        # remove lost relationships
        if rem_list:
            # one side
            db.engine.execute(Relative.delete().where(db.and_(Relative.c.citizen_id == db_citizen_id,
                                                              Relative.c.relative_id.in_(rem_list))))
            # opposite side
            db.engine.execute(Relative.delete().where(db.and_(Relative.c.citizen_id.in_(rem_list),
                                                              Relative.c.relative_id == db_citizen_id)))
        # add new relationships
        if add_links:
            db.engine.execute(Relative.insert(), add_links)

        return db_citizen_id

    @staticmethod
    def merge_relatives(citizen_relatives: list, id_list: List[int]) -> dict:
        """
        Maps database ids to citizen_ids and merges joined citizen relationships
        rows from database into properly serializable format.
        Converts citizen from raw format to a named dict as a side-effect.
        :param citizen_relatives: list of RowProxy of citizen and relative data
        :param id_list: list of ids to citizen_ids
        :return: citizen dict with relatives
        """
        citizen_relatives = [dict(citizen_relative) for citizen_relative in citizen_relatives]
        citizen = dict(citizen_relatives[0])

        if citizen['relative_id']:
            id_map = {k: v for k, v in id_list}
            relatives = [id_map[entry['relative_id']] for entry in citizen_relatives]
        else:
            relatives = []

        citizen['relatives'] = relatives

        del citizen['relative_id']

        return citizen

    def patch(self, import_id, citizen_id):
        """
        Patch request handler
        """
        try:
            citizen_part = citizenSchema.load(request.json, partial=True)
        except ValidationError as ex:
            return {'message': f'Validation error', 'errors': ex.messages}, 400
        except KeyError as ex:
            return {'message': f'Expected key {ex} not found in the request body'}, 400
        except TypeError as ex:
            return {'message': f'Malformed data', 'errors': ex}, 400

        if 'citizen_id' in citizen_part:
            return {'message': 'citizen_id can not be patched'}, 400

        if 'relatives' in citizen_part:  # resolve relative link changes, update and get citizen by id
            requested_relatives = citizen_part['relatives']
            try:
                db_citizen_id = self.process_relatives(import_id, citizen_id, requested_relatives)
            except ValidationError as ex:
                return {'message': f'Validation error', 'errors': ex.messages}, 400
            except KeyError:
                # can't tell whats exactly wrong as its up to database querying result being empty
                # or did I just masked out a weird bug? Probably not a good solution.
                return {'message': f'import_id {import_id} or citizen_id {citizen_id} not found'}, 404

            if len(citizen_part) > 1:  # this means we do have something to update besides relatives
                db.engine.execute(Citizen.update().where(Citizen.c.id == db_citizen_id), citizen_part)

            citizen = db.engine.execute(db.select([Citizen]).where(Citizen.c.id == db_citizen_id)).fetchone()
            response = citizenSchema.dump(citizen)
            # I know, but this saves precious time
            response['relatives'] = citizen_part['relatives']

        else:  # update and get citizen by import_id and citizen_id as we don't know the absolute id

            update_result = db.engine.execute(Citizen.update()
                                              .where(Citizen.c.import_id == import_id)
                                              .where(Citizen.c.citizen_id == citizen_id),
                                              citizen_part
                                              )

            # a dirty way of citizen_id and import_id validation
            # it relies on database to report 0 rows updated which means
            # either of parameters are missing
            if update_result.rowcount != 1:
                return {'message': f'citizen_id or import_id not found'}, 404

            join = Citizen.outerjoin(Relative, Relative.c.citizen_id == Citizen.c.id)
            citizen_relatives = db.engine.execute(db.select([Citizen, Relative.c.relative_id])
                                                  .where(Citizen.c.import_id == import_id)
                                                  .where(Citizen.c.citizen_id == citizen_id)
                                                  .select_from(join)).fetchall()

            # get list of ids to citizen_ids to resolve relatives
            id_list = db.engine.execute(
                db.select([Citizen.c.id, Citizen.c.citizen_id]).where(Citizen.c.import_id == import_id)
            ).fetchall()

            citizen = self.merge_relatives(citizen_relatives, id_list)
            response = citizenSchema.dump(citizen)

        return response, 200


class GetCitizens(Resource):
    """
        Serves /imports/<int:import_id>/citizens endpoint
    """

    @staticmethod
    def merge_by_relatives(raw_citizens: List) -> List[Dict]:
        """
        Maps database ids to citizen_ids and merges joined citizen relationships
        rows from database into properly serializable format.
        Converts citizens from raw format to named dicts as a side-effect.
        :param raw_citizens: list of RowProxy
        :return: list of citizens where each citizen is a dict
        """
        prev_id = 0
        citizens = [dict(raw_citizen) for raw_citizen in raw_citizens]
        id_map = {citizen['id']: citizen['citizen_id'] for citizen in citizens}
        result = []
        for citizen in citizens:
            relative_id = citizen['relative_id']
            if prev_id == citizen['citizen_id']:
                result[-1]['relatives'].append(id_map[relative_id])
            else:
                del citizen['relative_id']
                if relative_id:
                    citizen['relatives'] = [id_map[relative_id]]
                else:
                    citizen['relatives'] = []
                result.append(citizen)
            prev_id = citizen['citizen_id']
        return result

    def get(self, import_id):
        """
        Get request handler
        """

        join = Citizen.outerjoin(Relative, Relative.c.citizen_id == Citizen.c.id)
        raw_citizens = db.engine.execute(
            db.select([Citizen, Relative.c.relative_id])
                .where(Citizen.c.import_id == import_id)
                .order_by(Citizen.c.citizen_id).select_from(join)
        ).fetchall()

        # form relatives lists
        citizens = self.merge_by_relatives(raw_citizens)

        # looks like import_id not found database
        # this not the best way to check this, probably
        # but the idea was to reduce database queries amount
        if not citizens:
            return {'message': f'no data found for import_id: {import_id}'}, 404

        return {'data': citizensSchema.dump(citizens)}


class GetBirthdays(Resource):
    """
        Serves /imports/<int:import_id>/citizens/birthdays endpoint
    """

    @staticmethod
    def get(import_id):
        """
        Get request handler
        """

        # resulting dict template
        months_dict: Dict[int, List] = {x: [] for x in range(1, 13)}

        # get ids, citizen_ids, birthdays, relatives
        join = Citizen.outerjoin(Relative, Relative.c.citizen_id == Citizen.c.id)
        raw_citizens = db.engine.execute(
            db.select([Citizen.c.id, Citizen.c.citizen_id, Citizen.c.birth_date, Relative.c.relative_id])
                .where(Citizen.c.import_id == import_id)
                .order_by(Citizen.c.citizen_id)
                .select_from(join)
        ).fetchall()

        # pack them into dicts
        citizens_relatives = [dict(entry) for entry in raw_citizens]

        # empty database response
        if not citizens_relatives:
            return {'message': f'import_id {import_id} not found'}, 404

        id_bd_map = {x['id']: {'citizen_id': x['citizen_id'], 'month': x['birth_date'].month}
                     for x in citizens_relatives}

        # aggregation storage: citizen_id -> month -> number of presents
        presents = {}

        for citizen_relative in citizens_relatives:
            db_citizen_id = citizen_relative['id']
            citizen_id = id_bd_map[db_citizen_id]['citizen_id']

            db_relative_id = citizen_relative['relative_id']
            if not db_relative_id:  # no relatives :(
                continue

            relative_birth_month = id_bd_map[db_relative_id]['month']

            try:
                presents[citizen_id][relative_birth_month] += 1
            except KeyError:
                try:
                    presents[citizen_id][relative_birth_month] = 1
                except KeyError:
                    presents[citizen_id] = {relative_birth_month: 1}

        # build response from aggregation storage

        for citizen_key in presents:
            for month_key in presents[citizen_key]:
                months_dict[month_key].append({
                    'citizen_id': citizen_key,
                    'presents': presents[citizen_key][month_key]
                })

        return {'data': months_dict}, 200


class GetAges(Resource):
    """
        Serves /imports/<int:import_id>/towns/stat/percentile/age endpoint
    """

    @staticmethod
    def get(import_id):
        """
        Get request handler
        """

        raw_town_birthdays = db.engine.execute(
            db.select([Citizen.c.town, Citizen.c.birth_date])
                .where(Citizen.c.import_id == import_id)
                .order_by(Citizen.c.town)
        ).fetchall()

        town_birthdays = [dict(entry) for entry in raw_town_birthdays]

        if not town_birthdays:
            return {'message': f'import_id {import_id} not found'}, 404

        # keeps ages lists by towns
        towns_ages = {}

        for town_birthday in town_birthdays:
            town = town_birthday['town']
            birth_date = town_birthday['birth_date']
            age = relativedelta(datetime.utcnow(), birth_date).years
            try:
                towns_ages[town].append(age)
            except KeyError:
                towns_ages[town] = [age]

        response = []

        for town, ages in towns_ages.items():
            p50, p75, p99 = numpy.percentile(ages, [50, 75, 99])
            response.append({
                'town': town,
                'p50': p50,
                'p75': p75,
                'p99': p99
            })

        return {'data': response}, 200
