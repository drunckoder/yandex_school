from yandex_school import app, api
from yandex_school.resources import CreateImport, PatchCitizen, GetCitizens, GetBirthdays, GetAges

api.add_resource(CreateImport, '/imports')
api.add_resource(PatchCitizen, '/imports/<int:import_id>/citizens/<int:citizen_id>')
api.add_resource(GetCitizens, '/imports/<int:import_id>/citizens')
api.add_resource(GetBirthdays, '/imports/<int:import_id>/citizens/birthdays')
api.add_resource(GetAges, '/imports/<int:import_id>/towns/stat/percentile/age')

if __name__ == '__main__':
    app.run()
