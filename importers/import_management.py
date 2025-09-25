from models import Project, Screen, Plate

def import_project(session, group_name):
    project = session.query(Project).filter_by(group_name=group_name).first()
    if not project:
        project = Project(group_name=group_name)
        session.add(project)
    return project

def import_screen(session, project, screen_name, barcode, description=""):
    screen = session.query(Screen).filter_by(barcode=barcode).first()
    if not screen:
        screen = Screen(screen_name=screen_name, screen_description=description, barcode=barcode)
        project.screens.append(screen)
    return screen

def import_plate(session, screen, plate_name, barcode, date_experiment):
    plate = session.query(Plate).filter_by(barcode=barcode).first()
    if not plate:
        plate = Plate(plate_name=plate_name, barcode=barcode, date_experiment=str(date_experiment))
        screen.plates.append(plate)
    return plate