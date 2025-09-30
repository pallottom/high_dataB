from models import Project, Screen, Plate

def import_project(session, group_name):
    project = session.query(Project).filter_by(group_name=group_name).first()
    if not project:
        project = Project(group_name=group_name)
        session.add(project)
        session.commit()
    return project


def import_screen(session, project, screen_number, barcode, description):
    screen = session.query(Screen).filter_by(screen_number=screen_number, project=project).first()
    if screen:
        # Update the existing screen if it already exists
        screen.screen_description = description
        screen.barcode = barcode
    else:
        # Create a new screen if it doesn't exist
        screen = Screen(screen_number=screen_number, screen_description=description, barcode=barcode, project=project)
        session.add(screen)
    session.commit()
    return screen


def import_plate(session, screen, plate_name, barcode, date_experiment, project):
    plate = session.query(Plate).filter_by(barcode=barcode).first()
    if plate:
        # Update the existing plate if it already exists
        plate.plate_name = plate_name
        plate.date_experiment = str(date_experiment)
        plate.screen = screen
        plate.project = project

    else:
        # Create a new plate if it doesn't exist
        plate = Plate(plate_name=plate_name, barcode=barcode, date_experiment=str(date_experiment))
        screen.plates.append(plate)
        session.add(plate)
    session.commit()
    return plate